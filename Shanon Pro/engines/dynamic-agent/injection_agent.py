"""
Injection Agent — Autonomous browser-based vulnerability exploitation.

Implements the "POC-or-it-didn't-happen" validation principle:
- No finding is reported as a vulnerability without dynamic evidence
- Every confirmed vulnerability has an associated evidence package
- Evidence includes screenshot, HAR, and behavioral indicators
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response

from .models import (
    ExploitAttempt,
    ExploitResult,
    ExploitStatus,
    ExploitTask,
    InjectionPoint,
    POCStatus,
    ValidationEvidence,
    VulnType,
)
from .playwright_mapper import PlaywrightScriptMapper
from .poc_validator import POCValidator
from .strategies import ExploitStrategy, StrategyRegistry
from .utils import AutonomousFix

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for the Injection Agent."""
    browser_type: str = "chromium"
    headless: bool = True
    proxy_url: Optional[str] = None     # mitmproxy for traffic capture
    
    # Browser behavior
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-US"
    
    # Execution limits
    max_navigation_timeout: int = 30000
    max_action_timeout: int = 10000
    page_pool_size: int = 3
    
    # Evidence collection
    screenshot_on_every_step: bool = False
    record_video: bool = True
    capture_har: bool = True


class InjectionAgent:
    """
    Autonomous injection testing agent using browser automation.
    
    Core capabilities:
    1. Maps static analysis findings to dynamic browser interactions
    2. Executes exploit strategies with behavioral validation
    3. Collects immutable evidence (screenshots, HAR, network logs)
    4. Enforces "POC-or-it-didn't-happen" validation
    
    Usage:
        agent = InjectionAgent(config)
        result = await agent.execute(task)
        if result.is_validated:
            print(f"VULNERABLE: {result.reproduction_steps}")
    """
    
    def __init__(self, config: AgentConfig, strategy_registry: Optional[StrategyRegistry] = None):
        self.config = config
        self.strategy_registry = strategy_registry or StrategyRegistry()
        self.script_mapper = PlaywrightScriptMapper()
        self.validator = POCValidator()
        self.autofix = AutonomousFix()
        
        # Runtime state
        self._browser: Optional[Browser] = None
        self._contexts: list[BrowserContext] = []
        self._pages: list[Page] = []
        self._playwright = None
    
    async def start(self) -> None:
        """Initialize browser instance."""
        self._playwright = await async_playwright().start()
        
        browser_kwargs = {
            "headless": self.config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        }
        
        if self.config.proxy_url:
            browser_kwargs["proxy"] = {"server": self.config.proxy_url}
        
        if self.config.browser_type == "chromium":
            self._browser = await self._playwright.chromium.launch(**browser_kwargs)
        elif self.config.browser_type == "firefox":
            self._browser = await self._playwright.firefox.launch(**browser_kwargs)
        
        logger.info(f"Browser started: {self.config.browser_type}")
    
    async def stop(self) -> None:
        """Shutdown browser and cleanup."""
        for context in self._contexts:
            await context.close()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("Browser stopped")
    
    async def execute(self, task: ExploitTask) -> ExploitResult:
        """
        Execute exploit task with full evidence collection.
        
        Args:
            task: Exploit task from Correlation Engine
            
        Returns:
            ExploitResult with validation status and evidence
        """
        result = ExploitResult(
            task_id=task.task_id,
            finding_id=task.finding_id,
            status=ExploitStatus.RUNNING,
        )
        
        if not self._browser:
            await self.start()
        
        try:
            # Create isolated context for this task
            context = await self._create_isolated_context(task.task_id)
            page = await context.new_page()
            
            # Get strategies for this vulnerability type
            strategies = self.strategy_registry.get_strategies(task.vuln_type)
            
            if not strategies:
                result.status = ExploitStatus.ERROR
                result.summary = f"No strategies available for {task.vuln_type.value}"
                return result
            
            # Execute each strategy against each injection point
            for strategy in strategies:
                for injection_point in task.injection_points:
                    if result.is_validated:
                        break
                    
                    # Apply Autonomous Fix wrapper to the strategy execution
                    attempt = await self.autofix.wrap_execution(
                        self._execute_strategy,
                        page=page,
                        strategy=strategy,
                        task=task,
                        injection_point=injection_point,
                        context=context
                    )
                    
                    result.attempts.append(attempt)
                    
                    # Validate attempt results
                    validation = self.validator.validate(attempt, task.vuln_type)
                    
                    if validation == POCStatus.CONFIRMED:
                        result.poc_status = POCStatus.CONFIRMED
                        result.status = ExploitStatus.VALIDATED
                        result.confidence_score = 0.95
                        result.confirmed_evidence = attempt.evidence
                        result.summary = (
                            f"Confirmed {task.vuln_type.value} at "
                            f"{injection_point.parameter_name} using "
                            f"{strategy.name}"
                        )
                        result.reproduction_steps = self._generate_reproduction_steps(
                            attempt, task
                        )
                        break
                
                if result.is_validated:
                    break
            
            # If no strategy confirmed vulnerability
            if not result.is_validated:
                if result.attempts:
                    result.status = ExploitStatus.FAILED
                    result.poc_status = POCStatus.FALSE_POSITIVE
                    result.confidence_score = 0.1
                    result.summary = (
                        f"All {len(result.attempts)} exploit attempts failed. "
                        f"Static finding likely false positive."
                    )
                else:
                    result.status = ExploitStatus.ERROR
                    result.summary = "No attempts were made"
            
            result.completed_at = datetime.utcnow()
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            result.status = ExploitStatus.ERROR
            result.summary = f"Execution error: {str(e)}"
            result.completed_at = datetime.utcnow()
            return result
            
        finally:
            await context.close()
    
    async def _create_isolated_context(self, task_id: str) -> BrowserContext:
        """Create isolated browser context for task execution."""
        context_kwargs = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "user_agent": self.config.user_agent,
            "locale": self.config.locale,
            "java_script_enabled": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
        }
        
        # HAR recording
        if self.config.capture_har:
            har_path = f"/tmp/shannon/har/{task_id}.har"
            Path(har_path).parent.mkdir(parents=True, exist_ok=True)
            context_kwargs["record_har_path"] = har_path
        
        # Video recording
        if self.config.record_video:
            video_dir = f"/tmp/shannon/video/{task_id}"
            Path(video_dir).mkdir(parents=True, exist_ok=True)
            context_kwargs["record_video_dir"] = video_dir
        
        context = await self._browser.new_context(**context_kwargs)
        
        # Add stealth scripts
        await context.add_init_script("""
            // Hide automation indicators
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            window.chrome = { runtime: {} };
        """)
        
        self._contexts.append(context)
        return context
    
    async def _execute_strategy(
        self,
        page: Page,
        strategy: ExploitStrategy,
        task: ExploitTask,
        injection_point: InjectionPoint,
        context: BrowserContext,
    ) -> ExploitAttempt:
        """
        Execute a single exploit strategy against an injection point.
        
        Returns:
            ExploitAttempt with evidence
        """
        from datetime import datetime
        
        attempt = ExploitAttempt(
            task_id=task.task_id,
            strategy_used=strategy.name,
            injection_point=injection_point,
            started_at=datetime.utcnow(),
        )
        
        try:
            # Generate payloads for this strategy
            payloads = strategy.generate_payloads(injection_point, task.static_context)
            
            for payload in payloads:
                # Navigate to target
                await page.goto(
                    task.target_url,
                    wait_until="networkidle",
                    timeout=self.config.max_navigation_timeout,
                )
                
                # Inject payload
                response = await self._inject_payload(
                    page=page,
                    injection_point=injection_point,
                    payload=payload,
                    task=task,
                )
                
                if not response:
                    continue
                
                # Collect evidence
                evidence = await self._collect_evidence(
                    page=page,
                    response=response,
                    payload=payload,
                    injection_point=injection_point,
                    task=task,
                    context=context,
                )
                
                attempt.payload = payload
                attempt.evidence = evidence
                
                # Screenshot on success
                screenshot_path = f"/tmp/shannon/screenshots/{task.task_id}_{int(time.time())}.png"
                Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                evidence.screenshot_path = screenshot_path
                
                # Quick check for confirmation indicators
                if strategy.check_confirmation_indicators(evidence):
                    attempt.status = ExploitStatus.VALIDATED
                    break
                
                # Rate limiting
                await asyncio.sleep(task.delay_ms / 1000)
            
            if attempt.status != ExploitStatus.VALIDATED:
                attempt.status = ExploitStatus.FAILED
                
        except Exception as e:
            attempt.status = ExploitStatus.ERROR
            attempt.error_message = str(e)
            logger.error(f"Strategy {strategy.name} failed: {e}")
        
        attempt.completed_at = datetime.utcnow()
        return attempt
    
    async def _inject_payload(
        self,
        page: Page,
        injection_point: InjectionPoint,
        payload: str,
        task: ExploitTask,
    ) -> Optional[Response]:
        """
        Inject payload at the specified injection point.
        
        Handles form fields, query parameters, headers, and path injection.
        """
        location = injection_point.parameter_location
        name = injection_point.parameter_name
        
        try:
            if location in ["query", "body"]:
                # Form-based injection
                selector = f'[name="{name}"], [id="{name}"], input[placeholder*="{name}"]'
                element = await page.query_selector(selector)
                
                if element:
                    await element.fill(payload)
                    
                    # Submit form
                    submit = await page.query_selector(
                        'input[type="submit"], button[type="submit"]'
                    )
                    if submit:
                        response = await submit.click()
                        await page.wait_for_load_state("networkidle")
                        return response
                else:
                    # Direct URL manipulation
                    url = self._inject_url_parameter(task.target_url, name, payload)
                    return await page.goto(url, wait_until="networkidle")
                    
            elif location == "header":
                # Header injection - use fetch API via page.evaluate
                headers = {name: payload}
                result = await page.evaluate(
                    """async ({url, headers}) => {
                        const resp = await fetch(url, { headers });
                        return { status: resp.status, text: await resp.text() };
                    }""",
                    {"url": task.target_url, "headers": headers},
                )
                return None  # Header injection doesn't return Response object
                
            elif location == "path":
                # Path parameter injection
                url = task.target_url.replace(
                    f"{{{name}}}",
                    payload
                ).replace(
                    f":{name}",
                    payload
                )
                return await page.goto(url, wait_until="networkidle")
            
            else:
                # Generic: try to find and fill any matching input
                await page.fill(f'[name="{name}"]', payload)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
                
        except Exception as e:
            logger.warning(f"Payload injection failed: {e}")
            return None
    
    def _inject_url_parameter(self, url: str, param: str, value: str) -> str:
        """Inject parameter into URL query string."""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params[param] = [value]
        
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    
    async def _collect_evidence(
        self,
        page: Page,
        response: Response,
        payload: str,
        injection_point: InjectionPoint,
        task: ExploitTask,
        context: BrowserContext,
    ) -> ValidationEvidence:
        """Collect comprehensive evidence from exploit attempt."""
        # Get response content
        body = ""
        try:
            body = await page.content()
            if len(body) > 2000:
                body = body[:2000]
        except Exception:
            pass
        
        # Detect indicators
        indicators = []
        body_lower = body.lower()
        
        # SQL injection indicators
        if task.vuln_type == VulnType.SQL_INJECTION:
            sql_errors = [
                "sql syntax", "mysql_fetch", "pg_query", "ora-",
                "sqlserver", "jdbc", "sqlite3", "syntax error",
                "unexpected token", "unclosed quotation",
            ]
            for error in sql_errors:
                if error in body_lower:
                    indicators.append(f"sql_error:{error}")
            
            if "union select" in body_lower and "union" in payload.lower():
                indicators.append("union_select_reflected")
            
            time_based = await self._check_time_based(page, payload)
            if time_based:
                indicators.append("time_based_delay_confirmed")
        
        # XSS indicators
        if task.vuln_type == VulnType.CROSS_SITE_SCRIPTING:
            if payload in body:
                indicators.append("payload_reflected_unencoded")
            if "<script>" in body_lower or "javascript:" in body_lower:
                indicators.append("script_execution_detected")
        
        # Command injection indicators
        if task.vuln_type == VulnType.COMMAND_INJECTION:
            cmd_indicators = [
                "uid=", "root:", "bin/bash", "windows system32",
                "directory of", "volume in drive",
            ]
            for indicator in cmd_indicators:
                if indicator in body_lower:
                    indicators.append(f"command_output:{indicator}")
        
        evidence = ValidationEvidence(
            attempt_id="",  # Set by caller
            request_url=page.url,
            request_method=task.target_method,
            response_status=response.status if response else 0,
            response_body_preview=body,
            response_time_ms=0,
            indicators=indicators,
            har_path=context._impl_obj._options.get("recordHarPath"),
        )
        
        return evidence
    
    async def _check_time_based(self, page: Page, payload: str) -> bool:
        """Check if time-based SQL injection payload caused a delay."""
        # Check if payload contains time-based indicators
        time_indicators = ["sleep(", "benchmark(", "pg_sleep(", "waitfor delay"]
        if not any(ind in payload.lower() for ind in time_indicators):
            return False
        
        # Measure page load time
        start = time.time()
        await page.wait_for_load_state("networkidle", timeout=15000)
        elapsed = (time.time() - start) * 1000
        
        return elapsed > 4000  # Significant delay detected
    
    def _generate_reproduction_steps(
        self,
        attempt: ExploitAttempt,
        task: ExploitTask,
    ) -> str:
        """Generate human-readable reproduction steps."""
        ip = attempt.injection_point
        steps = [
            f"1. Navigate to: {task.target_url}",
            f"2. Locate the '{ip.parameter_name}' input field",
            f"   (Parameter location: {ip.parameter_location})",
            f"3. Enter the following payload:",
            f"   ```",
            f"   {attempt.payload}",
            f"   ```",
            f"4. Submit the form/request",
            f"5. Observe the following indicators:",
        ]
        
        if attempt.evidence:
            for indicator in attempt.evidence.indicators:
                steps.append(f"   - {indicator}")
            
            steps.extend([
                f"",
                f"Evidence collected:",
                f"- Screenshot: {attempt.evidence.screenshot_path}",
                f"- HAR file: {attempt.evidence.har_path}",
                f"- Response status: {attempt.evidence.response_status}",
            ])
        
        return "\n".join(steps)


# Import needed for datetime
from datetime import datetime
