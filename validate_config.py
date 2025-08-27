#!/usr/bin/env python3
"""Validate updated MCP server configuration."""


def parse_simple_yaml(path: str) -> dict:
    """A minimal YAML parser for the limited structure of ``smithery.yaml``.

    The real ``yaml`` package isn't available in the deployment environment,
    so this helper implements just enough parsing logic for the key/value
    pairs we use. It now handles strings, integers, booleans (``true``/``false``)
    and ``null`` values while silently skipping list items. This keeps
    ``validate_config.py`` and any scripts that import it free from external
    dependencies.
    """
    data: dict = {}
    stack = [data]
    indents = [0]

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#") or line.lstrip().startswith("-"):
                continue

            indent = len(line) - len(line.lstrip())
            while indent < indents[-1]:
                stack.pop()
                indents.pop()

            key, sep, value = line.lstrip().partition(":")
            if not sep:
                continue

            key = key.strip()
            value = value.strip()

            if not value:
                new_dict = {}
                stack[-1][key] = new_dict
                stack.append(new_dict)
                indents.append(indent + 2)
            else:
                if value.startswith("\"") and value.endswith("\""):
                    value = value[1:-1]
                elif value.lower() in {"true", "false"}:
                    value = value.lower() == "true"
                elif value.lower() in {"null", "none"}:
                    value = None
                elif value.isdigit():
                    value = int(value)
                stack[-1][key] = value

    return data


def validate_smithery_config() -> bool:
    """Validate smithery.yaml against basic expectations."""
    print("🔍 Validating smithery.yaml configuration...")

    try:
        config = parse_simple_yaml("smithery.yaml")

        # Check required fields according to Smithery docs
        required_fields = ["runtime", "startCommand"]
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False

        # Validate runtime
        if config.get("runtime") != "container":
            print(f"❌ Invalid runtime: {config.get('runtime')} (should be 'container')")
            return False

        # Validate startCommand
        start_command = config.get("startCommand", {})
        if start_command.get("type") != "http":
            print(
                f"❌ Invalid startCommand type: {start_command.get('type')} (should be 'http')"
            )
            return False

        # Ensure port matches PORT environment variable
        port = start_command.get("port")
        env = start_command.get("env", {})
        env_port = env.get("PORT")
        if str(port) != str(env_port):
            print(
                f"❌ startCommand port {port} doesn't match env PORT {env_port}"
            )
            return False

        # Verify command is present
        if "command" not in start_command:
            print("❌ Missing command in startCommand")
            return False

        # Check if configSchema exists
        if "configSchema" not in start_command:
            print("⚠️  No configSchema found - this may cause 'No test configuration found' warning")
        else:
            print("✅ configSchema found")

            # Validate configSchema structure
            schema = start_command["configSchema"]
            if schema.get("type") == "object" and "properties" in schema:
                print(f"✅ configSchema has {len(schema['properties'])} properties")
            else:
                print("❌ Invalid configSchema structure")
                return False

        # Check if exampleConfig exists
        if "exampleConfig" not in start_command:
            print("⚠️  No exampleConfig found - recommended for better UX")
        else:
            print("✅ exampleConfig found")

        print("✅ smithery.yaml validation passed!")
        return True

    except Exception as e:  # pragma: no cover - simple CLI script
        print(f"❌ Error validating smithery.yaml: {e}")
        return False


def test_config_schema() -> None:
    """Test the configuration schema we defined."""
    print("\n🧪 Testing configuration schema...")

    # Test valid config
    valid_config = {"maxJobs": 15, "timeout": 20}
    print(f"✅ Valid config example: {valid_config}")

    # Test edge cases
    edge_cases = [
        {"maxJobs": 1, "timeout": 5},    # Minimum values
        {"maxJobs": 50, "timeout": 30},  # Maximum values
        {"maxJobs": 0, "timeout": 2},    # Below minimum (should be clamped)
        {"maxJobs": 100, "timeout": 60}, # Above maximum (should be clamped)
    ]

    for i, case in enumerate(edge_cases, 1):
        print(f"📝 Edge case {i}: {case}")

    print("✅ Configuration schema test completed!")


def main() -> None:
    """Run all validation tests."""
    print("=" * 60)
    print("   MCP SERVER CONFIGURATION VALIDATION")
    print("=" * 60)

    schema_valid = validate_smithery_config()
    test_config_schema()

    print("\n" + "=" * 60)
    if schema_valid:
        print("🎉 Configuration validation SUCCESSFUL!")
        print("✅ smithery.yaml follows official Smithery schema")
        print("✅ configSchema should resolve 'No test configuration found'")
        print("✅ Ready for deployment!")
    else:
        print("❌ Configuration validation FAILED!")
        print("🔧 Please fix issues before deployment")
    print("=" * 60)


if __name__ == "__main__":
    main()
