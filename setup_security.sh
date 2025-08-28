#!/bin/bash
# EPOCH5 Security System Build and Setup Script

# Exit on error, undefined vars, and propagate pipe failures
set -euo pipefail

# Base directory
BASE_DIR="./archive/EPOCH5"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Create required directories
setup_directories() {
    print_msg "$BLUE" "Setting up EPOCH5 Security directories..."
    
    mkdir -p "$BASE_DIR/"{audit,scripts}
    mkdir -p "$BASE_DIR/audit/"{logs,seals,scrolls,capsules}
    
    print_msg "$GREEN" "✓ Directories created"
}

# Run tests
run_tests() {
    print_msg "$BLUE" "Running EPOCH5 Security tests..."
    
    # Basic tests for epoch_audit.py
    print_msg "$YELLOW" "Testing EpochAudit module..."
    python3 -c "
import sys
from epoch_audit import EpochAudit
try:
    audit = EpochAudit(base_dir='$BASE_DIR')
    audit.log_event('test', 'Testing audit system')
    result = audit.enforce_ceiling('task_priority', 150)
    if result['capped'] and result['final_value'] == 100:
        print('✓ Ceiling enforcement test passed')
    else:
        print('✗ Ceiling enforcement test failed')
        sys.exit(1)
    scroll = audit.generate_audit_scroll()
    if scroll:
        print('✓ Audit scroll generation test passed')
    else:
        print('✗ Audit scroll generation test failed')
        sys.exit(1)
    print('All EpochAudit tests passed')
except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1)
"
    
    # Basic tests for agent_security.py (if it exists)
    if [ -f "agent_security.py" ]; then
        print_msg "$YELLOW" "Testing AgentSecurityController module..."
        python3 -c "
import sys
try:
    from agent_security import AgentSecurityController
    # Just test that it can be imported without errors
    print('✓ AgentSecurityController module loaded successfully')
except ImportError as e:
    if 'agent_monitor' in str(e):
        print('⚠ AgentMonitor module not found (normal in test environment)')
    else:
        print(f'Error: {str(e)}')
        sys.exit(1)
except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1)
"
    fi
    
    print_msg "$GREEN" "✓ Tests completed"
}

# Install emoji commands
setup_emoji_commands() {
    print_msg "$BLUE" "Setting up emoji commands..."
    
    # Create scripts directory if it doesn't exist
    mkdir -p "$BASE_DIR/scripts"
    
    # Create emoji audit scroll script
    cat > "$BASE_DIR/scripts/emoji_audit_scroll.sh" <<EOL
#!/bin/bash
# EPOCH5 Audit Scroll Script
# Access with emoji: 🧙🦿🤖

python3 epoch_audit.py scroll --output $BASE_DIR/audit/scrolls/audit_\$(date +%Y%m%d_%H%M%S).txt
echo "📜 Audit scroll generated at $BASE_DIR/audit/scrolls/"
EOL
    
    # Make it executable
    chmod +x "$BASE_DIR/scripts/emoji_audit_scroll.sh"
    
    # Create alias file
    cat > "$BASE_DIR/scripts/emoji_alias.sh" <<EOL
#!/bin/bash
# EPOCH5 Emoji aliases
# Source this file to use emoji commands

alias 🧙🦿🤖="$BASE_DIR/scripts/emoji_audit_scroll.sh"
echo "EPOCH5 emoji commands available: 🧙🦿🤖 (audit scroll)"
EOL
    
    # Make it executable
    chmod +x "$BASE_DIR/scripts/emoji_alias.sh"
    
    print_msg "$GREEN" "✓ Emoji commands set up"
    print_msg "$YELLOW" "To use emoji commands, run: source $BASE_DIR/scripts/emoji_alias.sh"
}

# Create cron job for scheduled audit tasks
setup_cron_job() {
    print_msg "$BLUE" "Setting up cron job for nightly audit..."
    
    # Create audit script
    cat > "$BASE_DIR/scripts/nightly_audit.sh" <<EOL
#!/bin/bash
# EPOCH5 Nightly Audit Script

# Set base directory
BASE_DIR="$BASE_DIR"

# Generate timestamp
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)

# Generate audit scroll
python3 epoch_audit.py scroll --output \$BASE_DIR/audit/scrolls/nightly_audit_\$TIMESTAMP.txt

# Verify audit log integrity
python3 epoch_audit.py verify --max-events 1000 > \$BASE_DIR/audit/logs/verification_\$TIMESTAMP.log
EOL
    
    # Make it executable
    chmod +x "$BASE_DIR/scripts/nightly_audit.sh"
    
    # Add to crontab (commented out by default for safety)
    print_msg "$YELLOW" "To add nightly audit to cron (runs at 3 AM), use this command:"
    print_msg "$YELLOW" "echo \"0 3 * * * $BASE_DIR/scripts/nightly_audit.sh\" | crontab -"
    
    print_msg "$GREEN" "✓ Cron job script created"
}

# Setup agent security controller
setup_security_controller() {
    print_msg "$BLUE" "Setting up agent security controller..."
    
    if [ -f "agent_security.py" ]; then
        # Make it executable
        chmod +x agent_security.py
        
        # Create configuration file
        cat > "$BASE_DIR/security_config.json" <<EOL
{
    "ceilings": {
        "task_priority": 100,
        "resource_allocation": 100,
        "message_rate": 20,
        "concurrent_tasks": 10,
        "execution_time": 3600,
        "token_usage": 10000
    },
    "security_policies": {
        "required_heartbeat_interval": 300,
        "max_agent_restart_attempts": 5,
        "daily_resource_quota": 1000
    }
}
EOL
        
        print_msg "$GREEN" "✓ Security controller setup complete"
    else
        print_msg "$YELLOW" "⚠ agent_security.py not found. Skipping security controller setup."
    fi
}

# Clean up old script files
cleanup_old_scripts() {
    print_msg "$BLUE" "Cleaning up old script files..."
    
    if [ -f "new addition please scan" ]; then
        print_msg "$YELLOW" "Removing 'new addition please scan'..."
        rm "new addition please scan"
    fi
    
    if [ -f "new additions please scan pt 2" ]; then
        print_msg "$YELLOW" "Removing 'new additions please scan pt 2'..."
        rm "new additions please scan pt 2"
    fi
    
    print_msg "$GREEN" "✓ Cleanup complete"
}

# Main function
main() {
    print_msg "$BLUE" "=== EPOCH5 Security System Build and Setup ==="
    
    # Create directories
    setup_directories
    
    # Run tests
    run_tests
    
    # Set up emoji commands
    setup_emoji_commands
    
    # Set up cron job
    setup_cron_job
    
    # Set up security controller
    setup_security_controller
    
    # Clean up old script files
    cleanup_old_scripts
    
    print_msg "$GREEN" "=== EPOCH5 Security System Setup Complete ==="
    print_msg "$YELLOW" "Run 'python3 agent_security.py --help' for security controller commands"
    print_msg "$YELLOW" "Run 'python3 epoch_audit.py --help' for audit system commands"
}

# Run main function
main
