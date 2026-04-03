"""
Agent Memory Module

Provides shared memory and communication infrastructure for collaborative agents:
- Shared context where agents write insights
- Message bus for inter-agent communication
- Findings registry for tracking discoveries
- Conversation history
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json


# ============================================================================
# SHARED CONTEXT MANAGER
# ============================================================================

class SharedContext:
    """
    Shared memory space that all agents can read from and write to.
    Stores insights, findings, and intermediate results.
    """
    
    def __init__(self):
        self.context: Dict[str, Any] = {
            'insights': [],  # Agent insights/discoveries
            'findings': {},  # Structured findings by category
            'flags': [],     # Warnings/alerts
            'evidence': {},  # Supporting evidence for conclusions
            'metadata': {}   # Processing metadata
        }
        self.history: List[Dict] = []  # History of all updates
    
    def write_insight(self, agent_name: str, insight: str, category: str = 'general', 
                     confidence: float = 1.0, evidence: Optional[List] = None):
        """
        Write an insight to shared memory.
        
        Args:
            agent_name: Name of the agent writing the insight
            insight: The insight text
            category: Category of insight (e.g., 'clinical', 'lab_trend', 'symptom')
            confidence: Confidence level 0-1
            evidence: Supporting evidence
        """
        entry = {
            'agent': agent_name,
            'insight': insight,
            'category': category,
            'confidence': confidence,
            'evidence': evidence or [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.context['insights'].append(entry)
        self._log_update('write_insight', agent_name, entry)
    
    def write_finding(self, agent_name: str, finding_type: str, data: Dict):
        """
        Write a structured finding.
        
        Args:
            agent_name: Name of the agent
            finding_type: Type of finding (e.g., 'lab_trend', 'symptom', 'risk_factor')
            data: The finding data
        """
        if finding_type not in self.context['findings']:
            self.context['findings'][finding_type] = []
        
        finding = {
            'agent': agent_name,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.context['findings'][finding_type].append(finding)
        self._log_update('write_finding', agent_name, {finding_type: data})
    
    def write_flag(self, agent_name: str, flag_type: str, message: str, 
                   severity: str = 'medium', actionable: bool = True):
        """
        Write a flag/warning.
        
        Args:
            agent_name: Name of the agent
            flag_type: Type of flag (e.g., 'inconsistency', 'critical_value', 'missing_data')
            message: Flag message
            severity: 'low', 'medium', 'high', 'critical'
            actionable: Whether this flag requires action
        """
        flag = {
            'agent': agent_name,
            'type': flag_type,
            'message': message,
            'severity': severity,
            'actionable': actionable,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.context['flags'].append(flag)
        self._log_update('write_flag', agent_name, flag)
    
    def read_insights(self, category: Optional[str] = None, 
                     agent: Optional[str] = None) -> List[Dict]:
        """
        Read insights from shared memory.
        
        Args:
            category: Filter by category (optional)
            agent: Filter by agent name (optional)
            
        Returns:
            List of matching insights
        """
        insights = self.context['insights']
        
        if category:
            insights = [i for i in insights if i['category'] == category]
        if agent:
            insights = [i for i in insights if i['agent'] == agent]
        
        return insights
    
    def read_findings(self, finding_type: Optional[str] = None) -> Dict[str, List]:
        """
        Read findings from shared memory.
        
        Args:
            finding_type: Specific type to retrieve (optional)
            
        Returns:
            Findings dictionary or specific type list
        """
        if finding_type:
            return self.context['findings'].get(finding_type, [])
        return self.context['findings']
    
    def read_flags(self, severity: Optional[str] = None, 
                  actionable_only: bool = False) -> List[Dict]:
        """Read flags/warnings."""
        flags = self.context['flags']
        
        if severity:
            flags = [f for f in flags if f['severity'] == severity]
        if actionable_only:
            flags = [f for f in flags if f.get('actionable', False)]
        
        return flags
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all shared context."""
        return {
            'total_insights': len(self.context['insights']),
            'insights_by_category': self._count_by_field(self.context['insights'], 'category'),
            'total_findings': sum(len(v) for v in self.context['findings'].values()),
            'findings_by_type': {k: len(v) for k, v in self.context['findings'].items()},
            'total_flags': len(self.context['flags']),
            'flags_by_severity': self._count_by_field(self.context['flags'], 'severity'),
            'updates_count': len(self.history)
        }
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict:
        """Helper to count items by a field value."""
        counts = defaultdict(int)
        for item in items:
            counts[item.get(field, 'unknown')] += 1
        return dict(counts)
    
    def _log_update(self, action: str, agent: str, data: Any):
        """Log an update to history."""
        self.history.append({
            'action': action,
            'agent': agent,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def clear(self):
        """Clear all shared context (for testing/reset)."""
        self.context = {
            'insights': [],
            'findings': {},
            'flags': [],
            'evidence': {},
            'metadata': {}
        }
        self.history = []


# ============================================================================
# MESSAGE BUS
# ============================================================================

class MessageBus:
    """
    Message bus for inter-agent communication.
    Agents can send messages to specific agents or broadcast to all.
    """
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.mailboxes: Dict[str, List[Dict]] = defaultdict(list)
    
    def send_message(self, sender: str, recipient: str, message_type: str, 
                    content: Any, priority: int = 1):
        """
        Send a message from one agent to another.
        
        Args:
            sender: Sending agent name
            recipient: Receiving agent name (or 'all' for broadcast)
            message_type: Type of message ('query', 'response', 'alert', 'request')
            content: Message content
            priority: Priority 1-5 (1=highest)
        """
        message = {
            'id': f"{sender}-{recipient}-{len(self.messages)}",
            'sender': sender,
            'recipient': recipient,
            'type': message_type,
            'content': content,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat(),
            'read': False
        }
        
        self.messages.append(message)
        
        # Add to recipient's mailbox
        if recipient == 'all':
            # Broadcast to all agents
            for agent in self.mailboxes.keys():
                if agent != sender:
                    self.mailboxes[agent].append(message)
        else:
            self.mailboxes[recipient].append(message)
        
        return message['id']
    
    def read_messages(self, agent_name: str, unread_only: bool = True, 
                     message_type: Optional[str] = None) -> List[Dict]:
        """
        Read messages for an agent.
        
        Args:
            agent_name: Agent reading messages
            unread_only: Only return unread messages
            message_type: Filter by message type
            
        Returns:
            List of messages
        """
        messages = self.mailboxes.get(agent_name, [])
        
        if unread_only:
            messages = [m for m in messages if not m.get('read', False)]
        
        if message_type:
            messages = [m for m in messages if m['type'] == message_type]
        
        # Sort by priority (1=highest) and timestamp
        messages.sort(key=lambda m: (m['priority'], m['timestamp']))
        
        return messages
    
    def mark_read(self, message_id: str):
        """Mark a message as read."""
        for msg in self.messages:
            if msg['id'] == message_id:
                msg['read'] = True
                break
    
    def get_conversation(self, agent1: str, agent2: str) -> List[Dict]:
        """Get all messages between two agents."""
        conversation = []
        for msg in self.messages:
            if (msg['sender'] == agent1 and msg['recipient'] == agent2) or \
               (msg['sender'] == agent2 and msg['recipient'] == agent1):
                conversation.append(msg)
        
        conversation.sort(key=lambda m: m['timestamp'])
        return conversation
    
    def get_stats(self) -> Dict:
        """Get message bus statistics."""
        return {
            'total_messages': len(self.messages),
            'messages_by_type': self._count_by_field(self.messages, 'type'),
            'messages_by_sender': self._count_by_field(self.messages, 'sender'),
            'unread_messages': sum(1 for m in self.messages if not m.get('read', False))
        }
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict:
        """Helper to count items by field."""
        counts = defaultdict(int)
        for item in items:
            counts[item.get(field, 'unknown')] += 1
        return dict(counts)


# ============================================================================
# FINDINGS REGISTRY
# ============================================================================

class FindingsRegistry:
    """
    Central registry of all findings from agents.
    Tracks what each agent discovered and enables cross-validation.
    """
    
    def __init__(self):
        self.findings: Dict[str, List[Dict]] = defaultdict(list)
        self.agent_contributions: Dict[str, List[str]] = defaultdict(list)
    
    def register_finding(self, agent_name: str, finding_id: str, 
                        finding_type: str, data: Dict, confidence: float = 1.0):
        """
        Register a new finding.
        
        Args:
            agent_name: Agent that discovered the finding
            finding_id: Unique identifier for the finding
            finding_type: Type of finding
            data: Finding data
            confidence: Confidence level 0-1
        """
        finding = {
            'id': finding_id,
            'agent': agent_name,
            'type': finding_type,
            'data': data,
            'confidence': confidence,
            'validated_by': [],
            'contradicted_by': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.findings[finding_type].append(finding)
        self.agent_contributions[agent_name].append(finding_id)
    
    def validate_finding(self, finding_id: str, validator_agent: str, 
                        validation_data: Optional[Dict] = None):
        """
        Mark a finding as validated by another agent.
        
        Args:
            finding_id: The finding to validate
            validator_agent: Agent providing validation
            validation_data: Optional validation details
        """
        for findings_list in self.findings.values():
            for finding in findings_list:
                if finding['id'] == finding_id:
                    finding['validated_by'].append({
                        'agent': validator_agent,
                        'data': validation_data,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    return True
        return False
    
    def contradict_finding(self, finding_id: str, contradicting_agent: str, 
                          reason: str, evidence: Optional[Dict] = None):
        """
        Mark a finding as contradicted by another agent.
        
        Args:
            finding_id: The finding to contradict
            contradicting_agent: Agent providing contradiction
            reason: Reason for contradiction
            evidence: Supporting evidence
        """
        for findings_list in self.findings.values():
            for finding in findings_list:
                if finding['id'] == finding_id:
                    finding['contradicted_by'].append({
                        'agent': contradicting_agent,
                        'reason': reason,
                        'evidence': evidence,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    return True
        return False
    
    def get_findings_by_type(self, finding_type: str) -> List[Dict]:
        """Get all findings of a specific type."""
        return self.findings.get(finding_type, [])
    
    def get_findings_by_agent(self, agent_name: str) -> List[Dict]:
        """Get all findings from a specific agent."""
        all_findings = []
        for findings_list in self.findings.values():
            all_findings.extend([f for f in findings_list if f['agent'] == agent_name])
        return all_findings
    
    def get_validated_findings(self, min_validators: int = 1) -> List[Dict]:
        """Get findings validated by at least N other agents."""
        validated = []
        for findings_list in self.findings.values():
            for finding in findings_list:
                if len(finding['validated_by']) >= min_validators:
                    validated.append(finding)
        return validated
    
    def get_contradicted_findings(self) -> List[Dict]:
        """Get findings that have been contradicted."""
        contradicted = []
        for findings_list in self.findings.values():
            for finding in findings_list:
                if finding['contradicted_by']:
                    contradicted.append(finding)
        return contradicted
    
    def get_consensus(self) -> Dict[str, Any]:
        """
        Get consensus view of findings.
        Returns findings with high validation and low contradiction.
        """
        consensus = {
            'agreed': [],  # High validation, no contradiction
            'disputed': [],  # Both validation and contradiction
            'rejected': [],  # More contradiction than validation
            'unvalidated': []  # No validation yet
        }
        
        for findings_list in self.findings.values():
            for finding in findings_list:
                validated_count = len(finding['validated_by'])
                contradicted_count = len(finding['contradicted_by'])
                
                if validated_count > 0 and contradicted_count == 0:
                    consensus['agreed'].append(finding)
                elif validated_count > 0 and contradicted_count > 0:
                    consensus['disputed'].append(finding)
                elif contradicted_count > validated_count:
                    consensus['rejected'].append(finding)
                else:
                    consensus['unvalidated'].append(finding)
        
        return consensus


# ============================================================================
# INTEGRATED MEMORY SYSTEM
# ============================================================================

class AgentMemory:
    """
    Integrated memory system combining shared context, message bus, and findings.
    This is the main interface agents use for memory operations.
    """
    
    def __init__(self):
        self.shared_context = SharedContext()
        self.message_bus = MessageBus()
        self.findings_registry = FindingsRegistry()
        self.conversation_history: List[Dict] = []
    
    def log_agent_action(self, agent_name: str, action: str, details: Dict):
        """Log an agent's action to conversation history."""
        entry = {
            'agent': agent_name,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conversation_history.append(entry)
    
    def get_agent_history(self, agent_name: str) -> List[Dict]:
        """Get all actions by a specific agent."""
        return [entry for entry in self.conversation_history 
                if entry['agent'] == agent_name]
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get complete memory context for an agent to review."""
        return {
            'shared_insights': self.shared_context.read_insights(),
            'shared_findings': self.shared_context.read_findings(),
            'flags': self.shared_context.read_flags(),
            'my_messages': {},  # Populated per agent
            'validated_findings': self.findings_registry.get_validated_findings(),
            'disputed_findings': self.findings_registry.get_contradicted_findings(),
            'consensus': self.findings_registry.get_consensus()
        }
    
    def get_memory_summary(self) -> Dict:
        """Get summary of all memory systems."""
        return {
            'shared_context': self.shared_context.get_summary(),
            'message_bus': self.message_bus.get_stats(),
            'conversation_history': len(self.conversation_history),
            'total_findings': sum(len(v) for v in self.findings_registry.findings.values())
        }
    
    def export_memory(self) -> str:
        """Export all memory as JSON string."""
        export_data = {
            'shared_context': self.shared_context.context,
            'messages': self.message_bus.messages,
            'findings': dict(self.findings_registry.findings),
            'conversation_history': self.conversation_history
        }
        return json.dumps(export_data, indent=2)
    
    def clear_all(self):
        """Clear all memory (for testing)."""
        self.shared_context.clear()
        self.message_bus = MessageBus()
        self.findings_registry = FindingsRegistry()
        self.conversation_history = []


# Global memory instance (shared across all agents in a session)
AGENT_MEMORY = AgentMemory()


if __name__ == "__main__":
    # Test memory system
    print("=== Testing Memory Module ===\n")
    
    memory = AgentMemory()
    
    # Simulate agent interactions
    memory.shared_context.write_insight(
        'note_parser', 
        'Found fever and hypotension in clinical notes',
        category='symptom',
        confidence=0.95
    )
    
    memory.shared_context.write_finding(
        'lab_mapper',
        'lab_trend',
        {'parameter': 'lactate', 'trend': 'rising_sharply', 'values': [1.3, 2.4, 3.8]}
    )
    
    memory.shared_context.write_flag(
        'lab_mapper',
        'inconsistency',
        'Lactate trend shows sharp rise but no infection keywords found',
        severity='high',
        actionable=True
    )
    
    # Send messages
    memory.message_bus.send_message(
        'lab_mapper',
        'note_parser',
        'query',
        {'question': 'Did you find any infection-related symptoms?'},
        priority=1
    )
    
    memory.message_bus.send_message(
        'note_parser',
        'lab_mapper',
        'response',
        {'answer': 'Yes - found fever and hypotension'},
        priority=1
    )
    
    # Register findings
    memory.findings_registry.register_finding(
        'lab_mapper',
        'finding-001',
        'sepsis_indicator',
        {'lactate': 3.8, 'trend': 'rising'},
        confidence=0.9
    )
    
    memory.findings_registry.validate_finding(
        'finding-001',
        'note_parser',
        {'supporting_symptoms': ['fever', 'hypotension']}
    )
    
    # Log actions
    memory.log_agent_action('note_parser', 'parse_notes', {'notes_count': 3})
    memory.log_agent_action('lab_mapper', 'analyze_trends', {'trends_found': 5})
    
    # Print summary
    print("Memory Summary:")
    summary = memory.get_memory_summary()
    print(json.dumps(summary, indent=2))
    
    print("\n\nShared Context Summary:")
    ctx_summary = memory.shared_context.get_summary()
    print(json.dumps(ctx_summary, indent=2))
    
    print("\n\nMessages:")
    messages = memory.message_bus.read_messages('note_parser')
    for msg in messages:
        print(f"  From {msg['sender']}: {msg['content']}")
    
    print("\n\nConsensus:")
    consensus = memory.findings_registry.get_consensus()
    print(f"  Agreed: {len(consensus['agreed'])}")
    print(f"  Disputed: {len(consensus['disputed'])}")
    print(f"  Unvalidated: {len(consensus['unvalidated'])}")
