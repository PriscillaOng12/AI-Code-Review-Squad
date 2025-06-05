"""Tests for agent rule heuristics."""

from app.services.agents.security_agent import SecurityAgent
from app.services.agents.style_agent import StyleAgent
from app.services.agents.logic_agent import LogicAgent
from app.services.agents.performance_agent import PerformanceAgent
from app.services.agents.architecture_agent import ArchitectureAgent


def test_security_agent_detects_password():
    agent = SecurityAgent()
    findings = agent.analyze([('file.py', ['password = "x"'])])
    assert len(findings) == 1


def test_style_agent_detects_long_line():
    agent = StyleAgent()
    findings = agent.analyze([('file.py', ['a' * 130])])
    assert findings


def test_logic_agent_detects_todo():
    agent = LogicAgent()
    findings = agent.analyze([('file.py', ['# TODO: fix'])])
    assert findings


def test_performance_agent_detects_sleep():
    agent = PerformanceAgent()
    findings = agent.analyze([('file.py', ['time.sleep(1)'])])
    assert findings


def test_architecture_agent_detects_large_file():
    agent = ArchitectureAgent()
    lines = ['x'] * 201
    findings = agent.analyze([('file.py', lines)])
    assert findings