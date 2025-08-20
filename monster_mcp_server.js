#!/usr/bin/env node

import { Server as McpServer, ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import puppeteer from 'puppeteer';

const server = new McpServer({
  name: 'monster-jobs',
  version: '1.0.0'
}, {
  capabilities: {
    tools: {}
  }
});

const jobCache = new Map();
const jobIndex = new Map(); // job_number -> job
const jobIdIndex = new Map(); // job_id -> job
let sharedBrowser = null;

async function getBrowser() {
  if (!sharedBrowser) {
    sharedBrowser = await puppeteer.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  }
  return sharedBrowser;
}

// Register tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'search_monster_jobs',
        description: 'Search for jobs on Monster.com with location and radius filters',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Job search query (e.g., "business analyst", "software engineer")'
            },
            location: {
              type: 'string',
              description: 'Location to search (e.g., "Los Angeles, CA", "New York, NY")'
            },
            radius: {
              type: 'number',
              description: 'Search radius in miles',
              default: 5
            },
            recency: {
              type: 'string',
              enum: ['today', 'last+2+days', 'last+week', 'last+2+weeks'],
              description: 'Job posting recency filter',
              default: 'last+week'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results to return',
              default: 10
            }
          },
          required: ['query', 'location']
        }
      },
      {
        name: 'get_job_details',
        description: 'Get detailed information for a specific job from search results',
        inputSchema: {
          type: 'object',
          properties: {
            job_number: {
              type: 'number',
              description: 'The job number from search results (1-based index)'
            },
            job_id: {
              type: 'string',
              description: 'Alternative: Direct job ID if available'
            }
          }
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case 'search_monster_jobs':
      return await searchJobs(args);
    case 'get_job_details':
      return await getJobDetails(args);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

async function searchJobs(args) {
    const { query, location, radius = 5, recency = 'last+week', limit = 10 } = args;
    
    let browser;
    try {
      browser = await getBrowser();
      
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
      
      // Build search URL
      const searchUrl = buildSearchUrl(query, location, radius, recency);
      
      await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });
      
      // Wait for search results container
      await page.waitForSelector('#card-scroll-container', { timeout: 15000 });
      
      // Extract job listings
      const jobs = await page.evaluate((maxResults) => {
        const jobCards = document.querySelectorAll('#card-scroll-container .job-search-results-style__JobCardWrap-sc-30547e5b-4');
        const results = [];
        
        for (let i = 0; i < Math.min(jobCards.length, maxResults); i++) {
          const card = jobCards[i];
          
          try {
            // Extract job title
            const titleElement = card.querySelector('[data-testid="jobTitle"]');
            const title = titleElement?.textContent?.trim() || 'N/A';
            const jobUrl = titleElement?.href || '';
            
            // Extract job ID from button or URL
            const jobButton = card.querySelector('[data-testid="JobCardButton"]');
            const jobId = jobButton?.getAttribute('data-job-id') || 
                         jobUrl.match(/--([a-f0-9-]+)\?/)?.[1] || '';
            
            // Extract company
            const company = card.querySelector('[data-testid="company"]')?.textContent?.trim() || 'N/A';
            
            // Extract location
            const location = card.querySelector('[data-testid="jobDetailLocation"]')?.textContent?.trim() || 'N/A';
            
            // Extract posting date
            const recency = card.querySelector('[data-testid="jobDetailDateRecency"]')?.textContent?.trim() || 'N/A';
            
            // Extract salary if available
            const salaryElement = card.querySelector('[data-tagtype-testid="payTag"] .ds-tag-label');
            const salary = salaryElement?.textContent?.trim() || 'Not specified';
            
            // Create short description from available info
            let description = `${company} is hiring for a ${title} position in ${location}.`;
            if (salary !== 'Not specified') {
              description += ` Salary: ${salary}.`;
            }
            description += ` Posted: ${recency}.`;
            
            results.push({
              jobNumber: i + 1,
              title,
              company,
              location,
              salary,
              recency,
              description,
              jobId,
              jobUrl: jobUrl.startsWith('//') ? 'https:' + jobUrl : jobUrl
            });
          } catch (error) {
            // Skip failed job card parsing
          }
        }
        
        return results;
      }, limit);
      
      // Cache the results for detail retrieval
      const searchId = Date.now().toString();
      jobCache.set(searchId, jobs);
      
      // Index jobs for fast lookup
      jobs.forEach(job => {
        jobIndex.set(job.jobNumber, job);
        if (job.jobId) jobIdIndex.set(job.jobId, job);
      });
      
      // Clean old cache entries (keep last 10 searches)
      if (jobCache.size > 10) {
        const [oldestKey] = jobCache.keys();
        jobCache.delete(oldestKey);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              searchId,
              query,
              location,
              radius,
              totalResults: jobs.length,
              jobs: jobs.map(job => ({
                jobNumber: job.jobNumber,
                title: job.title,
                company: job.company,
                location: job.location,
                salary: job.salary,
                recency: job.recency,
                description: job.description
              }))
            }, null, 2)
          }
        ]
      };
      
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              details: 'Failed to search Monster.com jobs'
            }, null, 2)
          }
        ]
      };
    }
  }

async function getJobDetails(args) {
    const { job_number, job_id } = args;
    
    let targetJob;
    
    // Find job from indexed cache
    if (job_number) {
      targetJob = jobIndex.get(job_number);
    } else if (job_id) {
      targetJob = jobIdIndex.get(job_id);
    }
    
    if (!targetJob) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: 'Job not found in cache. Please run a search first.',
              available_jobs: Array.from(jobCache.values()).flat().map(job => ({
                jobNumber: job.jobNumber,
                title: job.title,
                company: job.company
              }))
            }, null, 2)
          }
        ]
      };
    }
    
    let browser;
    try {
      browser = await getBrowser();
      
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
      
      await page.goto(targetJob.jobUrl, { waitUntil: 'networkidle2', timeout: 30000 });
      
      // Wait for job details container
      await page.waitForSelector('#__next > div.main-layout-styles__Layout-sc-86e48e0f-0 > div.job-openings-style__SmallJobViewWrapper-sc-b9f61078-0 > div', { timeout: 15000 });
      
      // Extract detailed job information
      const jobDetails = await page.evaluate(() => {
        const container = document.querySelector('#__next > div.main-layout-styles__Layout-sc-86e48e0f-0 > div.job-openings-style__SmallJobViewWrapper-sc-b9f61078-0 > div');
        
        if (!container) {
          return { error: 'Job details container not found' };
        }
        
        // Extract various details
        const title = container.querySelector('h1')?.textContent?.trim() || 'N/A';
        const company = container.querySelector('[data-testid="company-name"]')?.textContent?.trim() || 'N/A';
        
        // Extract job description
        const descriptionElement = container.querySelector('[data-testid="job-description"], .job-description, [class*="description"]');
        const description = descriptionElement?.innerText?.trim() || 
                           container.querySelector('div[class*="JobDescription"], div[class*="job-description"]')?.innerText?.trim() ||
                           'Job description not available';
        
        // Extract requirements/qualifications
        const requirementsElement = container.querySelector('[data-testid="job-requirements"], .job-requirements, [class*="requirements"]');
        const requirements = requirementsElement?.innerText?.trim() || 'Requirements not specified';
        
        // Extract salary/compensation
        const salaryElement = container.querySelector('[data-testid="salary"], .salary, [class*="salary"], [class*="pay"]');
        const salary = salaryElement?.textContent?.trim() || 'Salary not specified';
        
        // Extract location
        const locationElement = container.querySelector('[data-testid="job-location"], .job-location, [class*="location"]');
        const location = locationElement?.textContent?.trim() || 'Location not specified';
        
        // Extract job type/employment type
        const jobTypeElement = container.querySelector('[data-testid="job-type"], .job-type, [class*="employment"]');
        const jobType = jobTypeElement?.textContent?.trim() || 'Job type not specified';
        
        return {
          title,
          company,
          location,
          salary,
          jobType,
          description,
          requirements,
          fullContent: container.innerText?.slice(0, 2000) // First 2000 chars as fallback
        };
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              jobNumber: targetJob.jobNumber,
              jobId: targetJob.jobId,
              url: targetJob.jobUrl,
              details: jobDetails
            }, null, 2)
          }
        ]
      };
      
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              details: 'Failed to retrieve job details',
              jobInfo: {
                jobNumber: targetJob.jobNumber,
                title: targetJob.title,
                company: targetJob.company,
                url: targetJob.jobUrl
              }
            }, null, 2)
          }
        ]
      };
    }
  }

function buildSearchUrl(query, location, radius, recency) {
    const baseUrl = 'https://www.monster.com/jobs/search';
    const params = new URLSearchParams({
      q: query,
      where: location,
      page: '1',
      rd: radius.toString(),
      so: 'm.h.sh'
    });
    
    if (recency && recency !== 'last+week') {
      params.append('recency', recency);
    }
    
    return `${baseUrl}?${params.toString()}`;
  }

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Monster.com Jobs MCP server running on stdio');
}

main().catch(console.error);