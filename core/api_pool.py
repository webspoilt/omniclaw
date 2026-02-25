#!/usr/bin/env python3
"""
OmniClaw API Pool
Manages multiple AI API keys with load balancing and failover
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import random

logger = logging.getLogger("OmniClaw.APIPool")


class APIStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RATE_LIMITED = "rate_limited"


@dataclass
class APIEndpoint:
    """Represents an API endpoint configuration"""
    provider: str
    key: str
    model: str
    base_url: Optional[str] = None
    status: APIStatus = APIStatus.HEALTHY
    last_used: float = 0
    request_count: int = 0
    error_count: int = 0
    avg_latency: float = 0
    rate_limit_reset: float = 0
    priority: int = 1  # Higher = more preferred
    capabilities: List[str] = field(default_factory=list)


class APIPool:
    """
    Manages a pool of AI API endpoints
    - Load balancing across multiple APIs
    - Health monitoring and failover
    - Rate limit handling
    - Cost optimization
    """
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.endpoint_order: List[str] = []
        self.health_check_interval = 60
        self.max_retries = 3
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_count": 0
        }
        
        # Start health check loop
        self._health_check_task = None
        
        logger.info("API Pool initialized")
    
    def add_endpoint(self, endpoint_id: str, config: Dict[str, Any]) -> APIEndpoint:
        """
        Add an API endpoint to the pool
        
        Args:
            endpoint_id: Unique identifier for this endpoint
            config: Configuration dict with provider, key, model, etc.
            
        Returns:
            The created APIEndpoint
        """
        endpoint = APIEndpoint(
            provider=config.get("provider", "openai"),
            key=config["key"],
            model=config.get("model", "gpt-4"),
            base_url=config.get("base_url"),
            priority=config.get("priority", 1),
            capabilities=config.get("capabilities", ["text", "chat"])
        )
        
        self.endpoints[endpoint_id] = endpoint
        self._update_endpoint_order()
        
        logger.info(f"Added endpoint {endpoint_id} ({endpoint.provider}/{endpoint.model})")
        return endpoint
    
    def remove_endpoint(self, endpoint_id: str):
        """Remove an endpoint from the pool"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            self._update_endpoint_order()
            logger.info(f"Removed endpoint {endpoint_id}")
    
    def _update_endpoint_order(self):
        """Update the endpoint priority order"""
        # Sort by priority (descending) and health status
        def sort_key(endpoint_id):
            ep = self.endpoints[endpoint_id]
            status_priority = {
                APIStatus.HEALTHY: 0,
                APIStatus.DEGRADED: 1,
                APIStatus.RATE_LIMITED: 2,
                APIStatus.UNHEALTHY: 3
            }
            return (status_priority.get(ep.status, 4), -ep.priority)
        
        self.endpoint_order = sorted(self.endpoints.keys(), key=sort_key)
    
    def get_endpoint(self, capability: Optional[str] = None, 
                     preferred_provider: Optional[str] = None) -> Optional[APIEndpoint]:
        """
        Get the best available endpoint
        
        Args:
            capability: Required capability
            preferred_provider: Preferred provider name
            
        Returns:
            Best available APIEndpoint or None
        """
        candidates = []
        
        for endpoint_id in self.endpoint_order:
            endpoint = self.endpoints[endpoint_id]
            
            # Skip unhealthy endpoints
            if endpoint.status == APIStatus.UNHEALTHY:
                continue
            
            # Skip rate-limited endpoints
            if endpoint.status == APIStatus.RATE_LIMITED:
                if time.time() < endpoint.rate_limit_reset:
                    continue
                else:
                    endpoint.status = APIStatus.HEALTHY
            
            # Check capability
            if capability and capability not in endpoint.capabilities:
                continue
            
            candidates.append((endpoint_id, endpoint))
        
        if not candidates:
            return None
        
        # Prefer specified provider
        if preferred_provider:
            for endpoint_id, endpoint in candidates:
                if endpoint.provider == preferred_provider:
                    return endpoint
        
        # Return highest priority candidate
        return candidates[0][1]
    
    async def execute_with_failover(self, operation: callable, 
                                    capability: Optional[str] = None,
                                    preferred_provider: Optional[str] = None) -> Any:
        """
        Execute an operation with automatic failover
        
        Args:
            operation: Async function that takes an APIEndpoint
            capability: Required capability
            preferred_provider: Preferred provider
            
        Returns:
            Operation result
        """
        attempted = []
        last_error = None
        
        for attempt in range(self.max_retries):
            endpoint = self.get_endpoint(capability, preferred_provider)
            
            if not endpoint:
                raise Exception("No healthy endpoints available")
            
            if endpoint in attempted:
                # Try next best endpoint
                for endpoint_id in self.endpoint_order:
                    candidate = self.endpoints[endpoint_id]
                    if candidate not in attempted and candidate.status != APIStatus.UNHEALTHY:
                        endpoint = candidate
                        break
            
            attempted.append(endpoint)
            
            try:
                start_time = time.time()
                result = await operation(endpoint)
                
                # Update stats
                latency = time.time() - start_time
                endpoint.avg_latency = (endpoint.avg_latency * endpoint.request_count + latency) / (endpoint.request_count + 1)
                endpoint.request_count += 1
                endpoint.last_used = time.time()
                
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                
                return result
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Handle rate limiting
                if "rate limit" in error_str or "429" in error_str:
                    endpoint.status = APIStatus.RATE_LIMITED
                    endpoint.rate_limit_reset = time.time() + 60
                    logger.warning(f"Rate limited on {endpoint.provider}, backing off")
                
                # Handle auth errors
                elif "authentication" in error_str or "401" in error_str or "403" in error_str:
                    endpoint.status = APIStatus.UNHEALTHY
                    logger.error(f"Auth error on {endpoint.provider}, marking unhealthy")
                
                # Handle other errors
                else:
                    endpoint.error_count += 1
                    if endpoint.error_count >= self.circuit_breaker_threshold:
                        endpoint.status = APIStatus.UNHEALTHY
                        logger.warning(f"Circuit breaker triggered for {endpoint.provider}")
                
                self.stats["retry_count"] += 1
                self._update_endpoint_order()
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        self.stats["failed_requests"] += 1
        raise Exception(f"All retries failed. Last error: {last_error}")
    
    async def health_check(self):
        """Perform health checks on all endpoints"""
        for endpoint_id, endpoint in self.endpoints.items():
            try:
                # Simple health check - try a minimal API call
                healthy = await self._check_endpoint_health(endpoint)
                
                if healthy:
                    if endpoint.status == APIStatus.UNHEALTHY:
                        logger.info(f"Endpoint {endpoint_id} recovered")
                    endpoint.status = APIStatus.HEALTHY
                    endpoint.error_count = 0
                else:
                    endpoint.error_count += 1
                    if endpoint.error_count >= 3:
                        endpoint.status = APIStatus.UNHEALTHY
                
            except Exception as e:
                logger.error(f"Health check failed for {endpoint_id}: {e}")
                endpoint.error_count += 1
                if endpoint.error_count >= 3:
                    endpoint.status = APIStatus.UNHEALTHY
        
        self._update_endpoint_order()
    
    async def _check_endpoint_health(self, endpoint: APIEndpoint) -> bool:
        """Check if an endpoint is healthy"""
        try:
            # Simple ping - can be customized per provider
            if endpoint.provider == "openai":
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=endpoint.key)
                response = await client.chat.completions.create(
                    model=endpoint.model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                return True
                
            elif endpoint.provider == "anthropic":
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=endpoint.key)
                response = await client.messages.create(
                    model=endpoint.model,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                return True
                
            elif endpoint.provider == "ollama":
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{endpoint.base_url or 'http://localhost:11434'}/api/tags"
                    ) as resp:
                        return resp.status == 200
            
            return False
            
        except Exception as e:
            logger.debug(f"Health check error: {e}")
            return False
    
    async def start_health_monitoring(self):
        """Start periodic health checks"""
        while True:
            await self.health_check()
            await asyncio.sleep(self.health_check_interval)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        endpoint_stats = {
            ep_id: {
                "provider": ep.provider,
                "model": ep.model,
                "status": ep.status.value,
                "requests": ep.request_count,
                "errors": ep.error_count,
                "avg_latency": ep.avg_latency
            }
            for ep_id, ep in self.endpoints.items()
        }
        
        return {
            **self.stats,
            "endpoints": endpoint_stats,
            "healthy_count": sum(1 for ep in self.endpoints.values() if ep.status == APIStatus.HEALTHY),
            "total_endpoints": len(self.endpoints)
        }
    
    def get_cost_estimate(self, tokens: int = 1000) -> Dict[str, float]:
        """Get cost estimate across providers"""
        # Approximate pricing (should be updated regularly)
        pricing = {
            "gpt-5": {"input": 0.05, "output": 0.10},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-4.6-opus": {"input": 0.015, "output": 0.075},
            "claude-4.6-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "gemini-3.1": {"input": 0.0015, "output": 0.005},
            "minimax-m2.5": {"input": 0.001, "output": 0.002},
            "kimi-2.5": {"input": 0.001, "output": 0.002},
            "glm-5": {"input": 0.001, "output": 0.002}
        }
        
        estimates = {}
        for ep_id, ep in self.endpoints.items():
            model_pricing = pricing.get(ep.model, {"input": 0.01, "output": 0.02})
            cost = (tokens / 1000) * (model_pricing["input"] + model_pricing["output"]) / 2
            estimates[ep_id] = cost
        
        return estimates
