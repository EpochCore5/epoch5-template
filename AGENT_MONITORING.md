# Agent Monitoring System

The EPOCH5 Agent Monitoring System provides a comprehensive solution for monitoring, communicating with, and managing all agents in the EPOCH5 ecosystem.

## Features

- **Real-time Agent Monitoring**: Track the status, health, and performance of all agents
- **Inter-Agent Communication**: Send messages, commands, tasks, and queries between agents
- **Performance Analytics**: Visualize agent reliability, task success rates, and latency metrics
- **Command Broadcasting**: Send commands to multiple agents based on type or capabilities
- **Task Assignment**: Intelligently assign tasks to the most suitable agents
- **Multiple Interfaces**: Web dashboard, CLI, and API access for different use cases

## Components

The monitoring system consists of several components:

1. **Agent Monitor Module** (`agent_monitor.py`): Core functionality for agent communication and monitoring
2. **Web Dashboard** (`agent_monitor_dashboard.sh`): Visual interface for monitoring and managing agents
3. **Command-Line Interface** (`agent_cli.py`): Quick terminal access for agent operations
4. **Message Handling System**: File-based message passing between agents

## Getting Started

### Using the Web Dashboard

The web dashboard provides a visual interface for monitoring and interacting with agents.

```bash
# Start the dashboard with default settings
./agent_monitor_dashboard.sh

# Customize host and port
./agent_monitor_dashboard.sh --host=127.0.0.1 --port=8080

# Run in debug mode
./agent_monitor_dashboard.sh --debug
```

Once started, access the dashboard at `http://localhost:8050` (or your custom host/port).

### Using the Command-Line Interface

The CLI provides quick access to monitoring and communication functions.

```bash
# List all registered agents
./agent_cli.py list

# Show detailed information for a specific agent
./agent_cli.py info <agent_did>

# Send a command to an agent
./agent_cli.py send <agent_did> <command> --parameters='{"param1": "value1"}'

# Broadcast a command to all agents of a specific type
./agent_cli.py broadcast <command> --agent-type=strategydeck

# Start real-time monitoring
./agent_cli.py monitor
```

Run `./agent_cli.py help` for a complete list of commands and options.

## Agent Message Protocol

Agents communicate using a standardized message format:

```json
{
  "message_id": "unique-message-id",
  "message_type": "command|task|query|notification|status_update",
  "content": {
    "key": "value"
  },
  "sender": "sender-agent-did",
  "recipient": "recipient-agent-did",
  "timestamp": "iso-timestamp",
  "priority": "normal|high|low"
}
```

Message Types:
- **command**: Execute a command on the agent
- **task**: Assign a task to be executed
- **query**: Request information from the agent
- **notification**: Inform the agent about an event
- **status_update**: Agent status information

## Integration with Your Agents

To make your agent compatible with the monitoring system:

1. Import the message handler from `agent_monitor.py`:
   ```python
   from agent_monitor import AgentMessage
   ```

2. Implement message handling in your agent's main loop:
   ```python
   def process_messages(self):
       # Check for messages addressed to this agent
       for message in self.get_pending_messages():
           if message.message_type == "command":
               self.handle_command(message.content)
           elif message.message_type == "task":
               self.handle_task(message.content)
   ```

3. Send status updates periodically:
   ```python
   def send_status_update(self):
       message = AgentMessage(
           message_type="status_update",
           content=self.get_status(),
           sender=self.agent_did
       )
       self.send_message(message)
   ```

## Extending the Monitoring System

The monitoring system is designed to be extensible:

- Add new message types for specialized communication
- Create custom dashboards for specific agent types
- Implement new visualization components for the web dashboard
- Add advanced analytics for agent performance optimization
