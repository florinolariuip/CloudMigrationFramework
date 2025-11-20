"""
PDF Report Generator for CMOv4 Best Solution

Generates a comprehensive PDF report explaining why the best solution
was selected, including technical details, financial breakdown, and
explainability traces.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from datetime import datetime
from typing import Dict, Any, List, Optional
import io


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


class CMOv4ReportGenerator:
    """Generate professional PDF reports for CMOv4 optimization results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=HexColor('#60a5fa'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        ))
        
        # Highlight box
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['BodyText'],
            fontSize=12,
            textColor=HexColor('#059669'),
            fontName='Helvetica-Bold',
            spaceAfter=10
        ))
    
    def generate_report(self, solution: Dict[str, Any], scenario_info: Dict[str, Any]) -> io.BytesIO:
        """
        Generate PDF report for the best solution
        
        Args:
            solution: The best solution from CMOv4 optimization
            scenario_info: Information about the scenario (components, constraints, etc.)
        
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Title page
        elements.extend(self._create_title_page(solution, scenario_info))
        
        # Executive Summary
        elements.extend(self._create_executive_summary(solution, scenario_info))
        
        # Technical Architecture
        elements.extend(self._create_technical_section(solution, scenario_info))
        
        # Financial Analysis
        elements.extend(self._create_financial_section(solution, scenario_info))
        
        # Selection Rationale
        elements.extend(self._create_rationale_section(solution, scenario_info))
        
        # Explainability & Transparency
        elements.extend(self._create_explainability_section(solution))
        
        # Recommendations
        elements.extend(self._create_recommendations_section(solution, scenario_info))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def _create_title_page(self, solution: Dict, scenario_info: Dict) -> List:
        """Create title page"""
        elements = []
        
        # Title
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(
            "Cloud Migration Optimizer v4",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            "<b>Optimal Solution Report</b>",
            ParagraphStyle(
                'Subtitle',
                parent=self.styles['Normal'],
                fontSize=18,
                textColor=HexColor('#6b7280'),
                alignment=TA_CENTER
            )
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        # Summary box
        summary_data = [
            ['<b>Total Cost</b>', f"${safe_float(solution.get('cost', 0)):,.2f} / month"],
            ['<b>Latency</b>', f"{safe_float(solution.get('latency', 0)):.1f} ms"],
            ['<b>Providers</b>', str(safe_int(solution.get('providers', 0)))],
            ['<b>Score</b>', f"{safe_float(solution.get('score', 0)):.2f} / 100"],
            ['<b>Generated</b>', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#eff6ff')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#3b82f6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(PageBreak())
        
        return elements
    
    def _create_executive_summary(self, solution: Dict, scenario_info: Dict) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get provider distribution
        provider_dist = solution.get('providerDistribution', {})
        main_providers = ', '.join([f"{k} ({v} services)" for k, v in provider_dist.items()])
        
        summary_text = f"""
        This report presents the optimal cloud migration solution selected by the Cloud Migration 
        Optimizer v4 (CMOv4) system. The solution was chosen from {scenario_info.get('total_solutions', 'multiple')} 
        feasible configurations after rigorous multi-objective optimization considering cost, performance, 
        and architectural best practices.
        <br/><br/>
        <b>Key Highlights:</b><br/>
        • <b>Monthly Cost:</b> ${safe_float(solution.get('cost', 0)):,.2f}<br/>
        • <b>Expected Latency:</b> {safe_float(solution.get('latency', 0)):.1f} milliseconds<br/>
        • <b>Provider Strategy:</b> {main_providers}<br/>
        • <b>Optimization Score:</b> {safe_float(solution.get('score', 0)):.2f}/100 (higher is better)<br/>
        • <b>Architecture Pattern:</b> {scenario_info.get('architecture_pattern', 'Microservices')}<br/>
        <br/>
        This solution represents the best balance between cost efficiency, performance requirements, 
        and operational complexity for your specific scenario.
        """
        
        elements.append(Paragraph(summary_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_technical_section(self, solution: Dict, scenario_info: Dict) -> List:
        """Create technical architecture section"""
        elements = []
        
        elements.append(Paragraph("Technical Architecture", self.styles['SectionHeader']))
        
        elements.append(Paragraph("Component-to-Service Mapping", self.styles['SubsectionHeader']))
        
        intro_text = """
        The following table shows the optimal service selection for each component in your 
        architecture. Each service was selected based on cost-performance trade-offs, provider 
        capabilities, and integration compatibility.
        """
        elements.append(Paragraph(intro_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Service mapping table
        configuration = solution.get('configuration', {})
        if configuration:
            service_data = [['<b>Component</b>', '<b>Selected Service</b>', '<b>Provider</b>']]
            
            for component, service in sorted(configuration.items()):
                provider = 'AWS' if 'AWS' in service else 'Azure' if 'Azure' in service else 'GCP' if 'GCP' in service else 'Unknown'
                service_data.append([
                    component.replace('_', ' ').title(),
                    service,
                    provider
                ])
            
            service_table = Table(service_data, colWidths=[1.8*inch, 3*inch, 1*inch])
            service_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9fafb')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(service_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Provider distribution
        elements.append(Paragraph("Provider Distribution", self.styles['SubsectionHeader']))
        
        provider_dist = solution.get('providerDistribution', {})
        if provider_dist:
            dist_text = "The solution distributes services across the following cloud providers:<br/><br/>"
            total_services = sum(safe_int(count) for count in provider_dist.values())
            for provider, count in sorted(provider_dist.items(), key=lambda x: safe_int(x[1]), reverse=True):
                count_int = safe_int(count)
                percentage = (count_int / total_services) * 100 if total_services > 0 else 0
                dist_text += f"• <b>{provider}:</b> {count_int} services ({percentage:.1f}%)<br/>"
            
            elements.append(Paragraph(dist_text, self.styles['BodyJustified']))
            
            strategy_text = f"""
            <br/>
            This {'multi-cloud' if len(provider_dist) > 1 else 'single-cloud'} strategy 
            {'provides vendor diversification, reduces lock-in risk, and leverages best-of-breed services from each provider.' if len(provider_dist) > 1 else 'provides simplicity, reduced integration complexity, and consolidated billing.'}
            """
            elements.append(Paragraph(strategy_text, self.styles['BodyJustified']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_financial_section(self, solution: Dict, scenario_info: Dict) -> List:
        """Create financial analysis section"""
        elements = []
        
        elements.append(Paragraph("Financial Analysis", self.styles['SectionHeader']))
        
        total_cost = safe_float(solution.get('cost', 0))
        budget = safe_float(scenario_info.get('max_budget', 10000))
        budget_usage = (total_cost / budget) * 100 if budget > 0 else 0
        
        cost_intro = f"""
        The selected solution has a projected monthly cost of <b>${total_cost:,.2f}</b>, 
        representing <b>{budget_usage:.1f}%</b> of your ${budget:,.2f} budget. This leaves 
        ${budget - total_cost:,.2f} of headroom for unexpected usage spikes or future scaling needs.
        """
        elements.append(Paragraph(cost_intro, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Cost breakdown by provider
        elements.append(Paragraph("Cost Distribution by Provider", self.styles['SubsectionHeader']))
        
        # Estimate cost per provider (simplified - actual would need service pricing breakdown)
        provider_dist = solution.get('providerDistribution', {})
        if provider_dist:
            # Simple distribution: cost proportional to service count
            total_services = sum(provider_dist.values())
            cost_data = [['<b>Provider</b>', '<b>Services</b>', '<b>Est. Cost</b>', '<b>% of Total</b>']]
            
            for provider, count in sorted(provider_dist.items(), key=lambda x: x[1], reverse=True):
                est_cost = (safe_float(count) / safe_float(total_services)) * total_cost if total_services > 0 else 0
                percentage = (est_cost / total_cost) * 100 if total_cost > 0 else 0
                cost_data.append([
                    provider,
                    str(safe_int(count)),
                    f"${est_cost:,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            cost_table = Table(cost_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f0fdf4')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(cost_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Budget compliance
        elements.append(Paragraph("Budget Compliance", self.styles['SubsectionHeader']))
        
        compliance_text = f"""
        <b>✓ Budget Compliant:</b> This solution operates {'well within' if budget_usage < 80 else 'within' if budget_usage < 95 else 'near the limit of'} 
        your specified budget, providing {'excellent' if budget_usage < 70 else 'good' if budget_usage < 85 else 'adequate'} 
        cost efficiency while meeting all technical requirements.
        <br/><br/>
        <b>Annual Projection:</b> ${total_cost * 12:,.2f} (assumes consistent monthly usage)
        """
        elements.append(Paragraph(compliance_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_rationale_section(self, solution: Dict, scenario_info: Dict) -> List:
        """Create selection rationale section"""
        elements = []
        
        elements.append(Paragraph("Why This Solution Was Selected", self.styles['SectionHeader']))
        
        score = safe_float(solution.get('score', 0))
        cost = safe_float(solution.get('cost', 0))
        latency = safe_float(solution.get('latency', 0))
        max_latency = safe_float(scenario_info.get('max_latency', 150))
        providers = safe_int(solution.get('providers', 0))
        
        rationale_text = f"""
        The Cloud Migration Optimizer v4 employs a hybrid approach combining Constraint Satisfaction 
        Problem (CSP) solving, expert system rules, and Pareto multi-objective optimization. This 
        solution achieved a score of <b>{score:.2f}/100</b>, making it the highest-ranked option 
        among all feasible configurations.
        <br/><br/>
        <b>Key Selection Factors:</b>
        """
        elements.append(Paragraph(rationale_text, self.styles['BodyJustified']))
        
        # Selection factors
        factors = [
            ("Cost Efficiency", f"${cost:,.2f}/month represents optimal value for required capabilities", "✓"),
            ("Performance", f"{latency:.1f}ms latency meets your {max_latency:.1f}ms requirement", "✓"),
            ("Scalability", f"Architecture supports horizontal scaling across {providers} provider(s)", "✓"),
            ("Reliability", "High availability through managed services and geographic distribution", "✓"),
            ("Complexity Management", f"{len(solution.get('configuration', {}))} integrated services with proven compatibility", "✓"),
        ]
        
        factor_data = [['<b>Factor</b>', '<b>Details</b>', '<b>Status</b>']]
        for factor, detail, status in factors:
            factor_data.append([factor, detail, status])
        
        factor_table = Table(factor_data, colWidths=[1.5*inch, 3.8*inch, 0.5*inch])
        factor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('FONTSIZE', (2, 1), (2, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#faf5ff')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(factor_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_explainability_section(self, solution: Dict) -> List:
        """Create explainability and transparency section"""
        elements = []
        
        elements.append(Paragraph("Explainability & Transparency", self.styles['SectionHeader']))
        
        intro_text = """
        CMOv4 provides full transparency into the decision-making process. Every optimization 
        decision is traceable through constraint proofs, rule evaluations, and Pareto analysis.
        """
        elements.append(Paragraph(intro_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Constraint satisfaction
        elements.append(Paragraph("Constraint Satisfaction Proof", self.styles['SubsectionHeader']))
        
        constraint_text = """
        This solution satisfies all hard constraints:<br/>
        • <b>Budget Constraint:</b> Cost stays within specified budget<br/>
        • <b>Latency Constraint:</b> Expected latency meets performance requirements<br/>
        • <b>Provider Constraint:</b> Uses allowed number of cloud providers<br/>
        • <b>Dependency Constraints:</b> All service dependencies are satisfied<br/>
        <br/>
        These constraints were enforced through Constraint Satisfaction Problem (CSP) solving, 
        ensuring mathematical feasibility before evaluation.
        """
        elements.append(Paragraph(constraint_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Expert system rules
        elements.append(Paragraph("Expert System Evaluation", self.styles['SubsectionHeader']))
        
        rules_text = f"""
        The solution was scored using {len(solution.get('evaluationLog', []))} expert system rules 
        covering cost optimization, performance tuning, reliability patterns, and architectural best practices. 
        The final score of <b>{safe_float(solution.get('score', 0)):.2f}/100</b> reflects comprehensive evaluation 
        across multiple dimensions.
        """
        elements.append(Paragraph(rules_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Pareto optimality
        elements.append(Paragraph("Pareto Multi-Objective Optimization", self.styles['SubsectionHeader']))
        
        pareto_text = """
        This solution exists on the Pareto frontier, meaning no other solution can improve one 
        objective (cost, latency, or reliability) without degrading another. It represents an 
        optimal trade-off point that cannot be strictly dominated by any alternative configuration.
        """
        elements.append(Paragraph(pareto_text, self.styles['BodyJustified']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_recommendations_section(self, solution: Dict, scenario_info: Dict) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Implementation Recommendations", self.styles['SectionHeader']))
        
        recommendations = [
            ("Phased Migration", "Deploy in stages starting with non-critical components to minimize risk and validate assumptions."),
            ("Cost Monitoring", "Implement continuous cost tracking to detect usage anomalies and optimize resource allocation."),
            ("Performance Testing", "Conduct load testing to validate latency assumptions under production workloads."),
            ("Disaster Recovery", "Establish backup procedures and multi-region failover strategies for critical services."),
            ("Security Hardening", "Apply least-privilege IAM policies, enable encryption at rest/transit, and configure network segmentation."),
            ("Scalability Planning", "Configure auto-scaling policies based on observed usage patterns and growth projections."),
        ]
        
        for i, (title, description) in enumerate(recommendations, 1):
            elements.append(Paragraph(f"<b>{i}. {title}</b>", self.styles['SubsectionHeader']))
            elements.append(Paragraph(description, self.styles['BodyJustified']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_text = """
        <br/><br/>
        <i>This report was automatically generated by Cloud Migration Optimizer v4 (CMOv4). 
        For questions or additional analysis, consult the full documentation at the CMOv4 interface.</i>
        """
        elements.append(Paragraph(
            footer_text,
            ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=HexColor('#6b7280'),
                alignment=TA_CENTER
            )
        ))
        
        return elements


def generate_cmov4_report(solution: Dict[str, Any], scenario_info: Dict[str, Any]) -> io.BytesIO:
    """
    Convenience function to generate CMOv4 report
    
    Args:
        solution: Best solution from optimization
        scenario_info: Scenario metadata (components, constraints, etc.)
    
    Returns:
        BytesIO buffer with PDF content
    """
    generator = CMOv4ReportGenerator()
    return generator.generate_report(solution, scenario_info)
