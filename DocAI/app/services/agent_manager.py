"""
Agent manager service for managing external agents.
"""
import os
import asyncio
import signal
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from app.services.base import BaseService, ServiceResult
from app.core.config import Config
from app.core.exceptions import (
    AgentConnectionError, AgentTimeoutError, AgentNotAvailableError
)


class AgentManager(BaseService):
    """
    Service for managing external agents like the browser agent.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        
        # Agent processes
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
        
        # Agent status
        self._status: Dict[str, Dict[str, Any]] = {
            'docai': {
                'initialized': True,
                'status': 'running',
                'started_at': datetime.utcnow()
            },
            'browser': {
                'initialized': False,
                'status': 'not_started',
                'process': None
            }
        }
        
        # Health check tasks
        self._health_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize the agent manager."""
        await super().initialize()
        
        # Start health monitoring for DocAI
        self._health_tasks['docai'] = asyncio.create_task(
            self._monitor_health('docai')
        )
    
    async def cleanup(self) -> None:
        """Clean up all agents and resources."""
        # Cancel health check tasks
        for task in self._health_tasks.values():
            if not task.done():
                task.cancel()
        
        # Stop all agents
        await self.stop_all_agents()
        
        await super().cleanup()
    
    async def start_browser_agent(self) -> ServiceResult:
        """
        Start the browser agent.
        
        Returns:
            ServiceResult
        """
        if self._status['browser']['initialized']:
            return ServiceResult.ok(
                message="Browser agent already running"
            )
        
        try:
            self._status['browser']['status'] = 'starting'
            
            # Check if launch script exists
            if not self.config.agent.browser_agent_path.exists():
                raise AgentConnectionError(
                    'browser',
                    f"Launch script not found: {self.config.agent.browser_agent_path}"
                )
            
            # Make script executable
            os.chmod(str(self.config.agent.browser_agent_path), 0o755)
            
            # Start browser agent process
            process = await asyncio.create_subprocess_exec(
                str(self.config.agent.browser_agent_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self._processes['browser'] = process
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.returncode is not None:
                stderr = await process.stderr.read()
                raise AgentConnectionError(
                    'browser',
                    f"Process exited with code {process.returncode}: {stderr.decode()}"
                )
            
            self._status['browser']['initialized'] = True
            self._status['browser']['status'] = 'running'
            self._status['browser']['started_at'] = datetime.utcnow()
            self._status['browser']['pid'] = process.pid
            
            # Start health monitoring
            self._health_tasks['browser'] = asyncio.create_task(
                self._monitor_health('browser')
            )
            
            self.logger.info(f"Browser agent started successfully (PID: {process.pid})")
            
            return ServiceResult.ok(
                {
                    'status': 'running',
                    'pid': process.pid,
                    'port': self.config.agent.browser_agent_port
                },
                message="Browser agent started successfully"
            )
            
        except Exception as e:
            self._status['browser']['status'] = 'error'
            self._status['browser']['initialized'] = False
            self._status['browser']['error'] = str(e)
            
            self.logger.error(f"Failed to start browser agent: {e}", exc_info=True)
            return ServiceResult.fail(f"Failed to start browser agent: {str(e)}")
    
    async def stop_browser_agent(self) -> ServiceResult:
        """
        Stop the browser agent.
        
        Returns:
            ServiceResult
        """
        if not self._status['browser']['initialized']:
            return ServiceResult.ok(
                message="Browser agent not running"
            )
        
        try:
            process = self._processes.get('browser')
            if process and process.returncode is None:
                # Send SIGTERM
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    # Force kill if not responding
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    await process.wait()
                
                self.logger.info("Browser agent stopped")
            
            # Cancel health task
            if 'browser' in self._health_tasks:
                self._health_tasks['browser'].cancel()
            
            # Update status
            self._status['browser']['initialized'] = False
            self._status['browser']['status'] = 'stopped'
            self._status['browser']['stopped_at'] = datetime.utcnow()
            
            # Remove from processes
            self._processes.pop('browser', None)
            
            return ServiceResult.ok(
                message="Browser agent stopped successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Error stopping browser agent: {e}", exc_info=True)
            return ServiceResult.fail(f"Failed to stop browser agent: {str(e)}")
    
    async def stop_all_agents(self) -> None:
        """Stop all running agents."""
        self.logger.info("Stopping all agents...")
        
        # Stop browser agent
        await self.stop_browser_agent()
        
        # Add other agents here as needed
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get status of a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent status dictionary
        """
        if agent_name not in self._status:
            raise AgentNotAvailableError(agent_name)
        
        return self._status[agent_name].copy()
    
    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents."""
        # Create clean copy without process objects
        status = {}
        for name, info in self._status.items():
            status[name] = {
                k: v for k, v in info.items()
                if k != 'process'
            }
        return status
    
    async def send_command(
        self,
        agent_name: str,
        command: str,
        params: Dict[str, Any]
    ) -> ServiceResult:
        """
        Send command to an agent.
        
        Args:
            agent_name: Agent name
            command: Command to send
            params: Command parameters
            
        Returns:
            ServiceResult with command response
        """
        if not self._status.get(agent_name, {}).get('initialized'):
            raise AgentNotAvailableError(agent_name)
        
        # TODO: Implement actual command sending via API or IPC
        
        return ServiceResult.ok(
            {
                'command': command,
                'params': params,
                'result': 'Command execution not yet implemented'
            }
        )
    
    async def _monitor_health(self, agent_name: str) -> None:
        """
        Monitor agent health.
        
        Args:
            agent_name: Agent to monitor
        """
        while True:
            try:
                await asyncio.sleep(self.config.agent.health_check_interval)
                
                if agent_name == 'browser':
                    process = self._processes.get('browser')
                    if process and process.returncode is not None:
                        self.logger.error(
                            f"Browser agent process died (exit code: {process.returncode})"
                        )
                        self._status['browser']['initialized'] = False
                        self._status['browser']['status'] = 'crashed'
                        
                        # TODO: Implement auto-restart logic
                
                # Add health check logic for other agents
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Health check error for {agent_name}: {e}",
                    exc_info=True
                )