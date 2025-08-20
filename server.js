#!/usr/bin/env node

import { Server as McpServer } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import * as cheerio from 'cheerio';

function timeoutSignal(ms) {
  try {
    if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
      return AbortSignal.timeout(ms);
    }
  } catch {}
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

const ListToolsRequestSchema = z.object({
  method: z.literal('tools/list'),
  params: z.object({}).optional(),
});

const CallToolRequestSchema = z.object({
  method: z.literal('tools/call'),
  params: z.object({
    name: z.string(),
    arguments: z.any(),
  }),
});

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
  
  try {
    switch (name) {
      case 'search_monster_jobs':
        return await searchJobs(args);
      case 'get_job_details':
        return await getJobDetails(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    console.error(`Error executing tool ${name}:`, error);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Failed to execute tool: ${error.message}`
          }, null, 2)
        }
      ]
    };
  }
});

async function searchJobs(args) {
    const { query, location, radius = 5, recency = 'last+week', limit = 10 } = args;
    console.log(`Searching Monster jobs: ${query} in ${location}`);
    
    try {
      const searchUrl = buildSearchUrl(query, location, radius, recency);
      console.log(`Fetching from: ${searchUrl}`);
      
      const response = await fetch(searchUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.status} ${response.statusText}`);
      }

      const html = await response.text();
      const $ = cheerio.load(html);

      const jobs = [];
      $('#card-scroll-container .job-search-results-style__JobCardWrap-sc-30547e5b-4').slice(0, limit).each((i, el) => {
        const card = $(el);
        const titleElement = card.find('[data-testid="jobTitle"]');
        const title = titleElement.text().trim() || 'N/A';
        let jobUrl = titleElement.attr('href') || '';
        if (jobUrl.startsWith('//')) {
          jobUrl = 'https:' + jobUrl;
        }

        const jobButton = card.find('[data-testid="JobCardButton"]');
        const jobId = jobButton.attr('data-job-id') || jobUrl.match(/--([a-f0-9-]+)\?/)?.[1] || '';
        
        const company = card.find('[data-testid="company"]').text().trim() || 'N/A';
        const location = card.find('[data-testid="jobDetailLocation"]').text().trim() || 'N/A';
        const recency = card.find('[data-testid="jobDetailDateRecency"]').text().trim() || 'N/A';
        const salary = card.find('[data-tagtype-testid="payTag"] .ds-tag-label').text().trim() || 'Not specified';

        let description = `${company} is hiring for a ${title} position in ${location}.`;
        if (salary !== 'Not specified') {
          description += ` Salary: ${salary}.`;
        }
        description += ` Posted: ${recency}.`;

        jobs.push({
          jobNumber: i + 1,
          title,
          company,
          location,
          salary,
          recency,
          description,
          jobId,
          jobUrl
        });
      });

      console.log(`Found ${jobs.length} jobs for: ${query} in ${location}`);
      
      const searchId = Date.now().toString();
      jobCache.set(searchId, jobs);
      
      jobs.forEach(job => {
        jobIndex.set(job.jobNumber, job);
        if (job.jobId) jobIdIndex.set(job.jobId, job);
      });
      
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
      console.error('Job search failed:', error);
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
    console.log(`Getting job details for job_number:${job_number} job_id:${job_id}`);
    
    let targetJob;
    
    if (job_number) {
      targetJob = jobIndex.get(job_number);
    } else if (job_id) {
      targetJob = jobIdIndex.get(job_id);
    }
    
    if (!targetJob) {
      console.warn('Job not found in cache');
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
    
    try {
      console.log(`Fetching job URL: ${targetJob.jobUrl}`);
      const response = await fetch(targetJob.jobUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch job details: ${response.status} ${response.statusText}`);
      }

      const html = await response.text();
      const $ = cheerio.load(html);

      const container = $('#__next > div.main-layout-styles__Layout-sc-86e48e0f-0 > div.job-openings-style__SmallJobViewWrapper-sc-b9f61078-0 > div');
      if (!container.length) {
        return { error: 'Job details container not found' };
      }

      const title = container.find('h1').text().trim() || 'N/A';
      const company = container.find('[data-testid="company-name"]').text().trim() || 'N/A';
      const description = container.find('[data-testid="job-description"], .job-description, [class*="description"]').text().trim() || 'Job description not available';
      const requirements = container.find('[data-testid="job-requirements"], .job-requirements, [class*="requirements"]').text().trim() || 'Requirements not specified';
      const salary = container.find('[data-testid="salary"], .salary, [class*="salary"], [class*="pay"]').text().trim() || 'Salary not specified';
      const location = container.find('[data-testid="job-location"], .job-location, [class*="location"]').text().trim() || 'Location not specified';
      const jobType = container.find('[data-testid="job-type"], .job-type, [class*="employment"]').text().trim() || 'Job type not specified';

      const jobDetails = {
        title,
        company,
        location,
        salary,
        jobType,
        description,
        requirements,
        fullContent: container.text().slice(0, 2000)
      };
      
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
      console.error('Failed to get job details:', error);
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
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Monster.com Jobs MCP server running on stdio');
  } catch (error) {
    console.error('Failed to start MCP server:', error);
    process.exit(1);
  }
}

main();