#!/bin/bash
# EPOCH5 Autonomous Control System Launcher
# Provides an integrated interface to all EPOCH5 autonomous components

echo "🧠 EPOCH5 Autonomous Control System"
echo "==================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if the system is initialized
if [ ! -d "archive/EPOCH5" ]; then
    echo "🔧 Initializing EPOCH5 system..."
    python3 integration.py setup-demo
    echo ""
fi

# Check if all components are available
missing_components=false

required_files=("meta_orchestrator.py" "self_healing.py" "adaptive_security.py" "ceiling_manager.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required component: $file"
        missing_components=true
    fi
done

if [ "$missing_components" = true ]; then
    echo "❌ Cannot start autonomous system with missing components."
    exit 1
fi

# Display menu
echo "Select an autonomous operation mode:"
echo "1) 🧠 Full Autonomous Mode (All Systems)"
echo "2) 🔒 Security-Focused Autonomy"
echo "3) 🔧 Self-Healing Focused Autonomy"
echo "4) 📊 Performance Optimization Autonomy"
echo "5) 📈 View System Status"
echo "6) ⚙️  Configure Autonomous Parameters"
echo "7) 🛑 Stop All Autonomous Systems"
echo "8) 📚 View System Improvement Recommendations"
echo "0) Exit"
echo ""

read -p "Enter your choice: " choice

start_meta_orchestrator() {
    echo "Starting Meta-Orchestrator with full autonomy..."
    python3 meta_orchestrator.py start
    echo "Meta-Orchestrator is running and coordinating all subsystems"
    echo "✓ Full autonomous mode activated"
}

start_security_autonomy() {
    echo "Starting Security-Focused Autonomous Mode..."
    python3 adaptive_security.py start
    echo "✓ Adaptive security system running in autonomous mode"
    echo "System will continuously monitor and respond to security threats"
}

start_healing_autonomy() {
    echo "Starting Self-Healing Focused Autonomous Mode..."
    python3 self_healing.py start
    echo "✓ Self-healing system running in autonomous mode"
    echo "System will automatically detect and recover from failures"
}

start_performance_autonomy() {
    echo "Starting Performance Optimization Autonomous Mode..."
    python3 ceiling_manager.py enforce config-1 budget 1000
    echo "✓ Performance optimization activated"
    echo "System will automatically adjust ceilings for optimal performance"
}

view_system_status() {
    echo "📊 System Status Dashboard"
    echo "--------------------------"
    
    # Check if meta-orchestrator is running
    if pgrep -f "meta_orchestrator.py" > /dev/null; then
        echo "🧠 Meta-Orchestrator: ✅ RUNNING"
        python3 meta_orchestrator.py status
    else
        echo "🧠 Meta-Orchestrator: ❌ STOPPED"
        
        # Check individual components
        if pgrep -f "adaptive_security.py" > /dev/null; then
            echo "🔒 Adaptive Security: ✅ RUNNING"
            python3 adaptive_security.py report
        else
            echo "🔒 Adaptive Security: ❌ STOPPED"
        fi
        
        if pgrep -f "self_healing.py" > /dev/null; then
            echo "🔧 Self-Healing: ✅ RUNNING"
            python3 self_healing.py status
        else
            echo "🔧 Self-Healing: ❌ STOPPED"
        fi
        
        if pgrep -f "ceiling_manager.py" > /dev/null; then
            echo "📈 Ceiling Manager: ✅ RUNNING"
            # Get current ceiling values
            python3 integration.py ceilings list
        else
            echo "📈 Ceiling Manager: ❌ STOPPED"
        fi
    fi
}

configure_parameters() {
    echo "⚙️  Autonomous System Configuration"
    echo "----------------------------------"
    echo "Select a component to configure:"
    echo "1) Meta-Orchestrator"
    echo "2) Adaptive Security"
    echo "3) Self-Healing"
    echo "4) Ceiling Management"
    echo "0) Back to main menu"
    
    read -p "Enter choice: " config_choice
    
    case $config_choice in
        1)
            echo "Configuring Meta-Orchestrator parameters..."
            python3 meta_orchestrator.py configure
            ;;
        2)
            echo "Configuring Adaptive Security parameters..."
            python3 adaptive_security.py configure
            ;;
        3)
            echo "Configuring Self-Healing parameters..."
            python3 self_healing.py configure
            ;;
        4)
            echo "Configuring Ceiling Management parameters..."
            read -p "Enter configuration ID: " config_id
            echo "Select service tier:"
            echo "1) Freemium ($0/month)"
            echo "2) Professional ($49.99/month)" 
            echo "3) Enterprise ($199.99/month)"
            read -p "Choose tier (1-3): " tier_choice
            
            case $tier_choice in
                1) tier="freemium" ;;
                2) tier="professional" ;;
                3) tier="enterprise" ;;
                *) tier="freemium" ;;
            esac
            
            python3 integration.py ceilings create "$config_id" --tier "$tier"
            ;;
        0)
            # Return to main menu
            ;;
        *)
            echo "❌ Invalid choice. Please try again."
            ;;
    esac
}

stop_autonomous_systems() {
    echo "🛑 Stopping all autonomous systems..."
    
    # Stop Meta-Orchestrator if running
    if pgrep -f "meta_orchestrator.py" > /dev/null; then
        python3 meta_orchestrator.py stop
        echo "✓ Meta-Orchestrator stopped"
    fi
    
    # Stop Adaptive Security if running
    if pgrep -f "adaptive_security.py" > /dev/null; then
        python3 adaptive_security.py stop
        echo "✓ Adaptive Security stopped"
    fi
    
    # Stop Self-Healing if running
    if pgrep -f "self_healing.py" > /dev/null; then
        python3 self_healing.py stop
        echo "✓ Self-Healing stopped"
    fi
    
    # Stop any remaining processes
    pkill -f "ceiling_manager.py" 2>/dev/null
    pkill -f "integration.py" 2>/dev/null
    
    echo "✓ All autonomous systems successfully stopped"
}

view_recommendations() {
    echo "📚 System Improvement Recommendations"
    echo "------------------------------------"
    
    # Get recommendations from each component
    echo "Meta-Orchestrator Recommendations:"
    if pgrep -f "meta_orchestrator.py" > /dev/null; then
        python3 meta_orchestrator.py status | grep -A 10 "Recommendations:" | tail -n 10
    else
        echo "❌ Meta-Orchestrator not running"
    fi
    
    echo ""
    echo "Self-Healing Recommendations:"
    if pgrep -f "self_healing.py" > /dev/null; then
        python3 self_healing.py status | grep -A 10 "Recommendations:" | tail -n 10
    else
        echo "❌ Self-Healing not running"
    fi
    
    echo ""
    echo "Security Recommendations:"
    if pgrep -f "adaptive_security.py" > /dev/null; then
        python3 adaptive_security.py report | grep -A 10 "Pattern Insights:" | tail -n 10
    else
        echo "❌ Adaptive Security not running"
    fi
    
    echo ""
    echo "Ceiling Management Recommendations:"
    python3 integration.py ceilings upgrade-rec config-1 2>/dev/null || echo "❌ No ceiling configurations available"
}

case $choice in
    1)
        start_meta_orchestrator
        ;;
    2)
        start_security_autonomy
        ;;
    3)
        start_healing_autonomy
        ;;
    4)
        start_performance_autonomy
        ;;
    5)
        view_system_status
        ;;
    6)
        configure_parameters
        ;;
    7)
        stop_autonomous_systems
        ;;
    8)
        view_recommendations
        ;;
    0)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please try again."
        ;;
esac
