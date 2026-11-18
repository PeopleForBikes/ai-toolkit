set positional-arguments

claude_base_settings := "claude/settings/base.json"

# Meta task running ALL the CI tasks at once.
ci: lint validate test

# Meta task running all the linters at once.
lint: lint-md

# Lint markdown files.
lint-md:
    npx --yes markdownlint-cli2 "**/*.md"

# Format markdown files.
fmt-md:
    npx --yes prettier --write --prose-wrap always "**/*.md"

# Meta task running all the validators at once.
validate: validate-plugins validate-nono-profiles

# Validate the plugin marketplace and its plugins.
validate-plugins:
    claude plugin validate .
    for plugin in plugins/*/; do claude plugin validate "$plugin"; done

# Validate the nono profiles.
validate-nono-profiles:
    for profile in nono/profiles/*.json; do nono profile validate "$profile"; done

# Run the tests of the helper scripts.
test:
    python3 -m unittest discover -s scripts -p '*.py' -v

# Install the nono profiles. Pass "force" to overwrite modified local copies.
install-nono-profiles mode="":
    python3 scripts/install_nono_profiles.py {{ if mode == "force" { "--force" } else if mode == "" { "" } else { error("mode must be empty or \"force\"") } }}

# Merge the shared Claude Code settings into a project's .claude/settings.json.
sync-claude-settings project:
    python3 scripts/sync_claude_settings.py "{{ claude_base_settings }}" "{{ project }}/.claude/settings.json"

# Check that a project's .claude/settings.json contains the shared settings.
check-claude-settings project:
    python3 scripts/sync_claude_settings.py "{{ claude_base_settings }}" "{{ project }}/.claude/settings.json" --check

# Use nono sandbox to login with Claude.
nono-claude-login:
    nono run --profile nolabs-ai/claude --allow-launch-services -- claude "/login"

# Use nono sandbox for Claude.
nono-claude profile="pfb-claude":
    nono run --allow-cwd --profile {{ profile }} -- claude

# Use nono sandbox for Claude -- restricted internet, skip-permissions.
nono-claude-danger profile="pfb-claude":
    nono run \
    --allow-cwd \
    --profile {{ profile }} \
    -- claude --dangerously-skip-permissions
