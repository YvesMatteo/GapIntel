"""
Premium Analysis - Visual Report Generator
Generates SVG charts and visualizations for reports.

Features:
- Hook effectiveness bar charts
- Thumbnail color performance heatmaps
- Content cluster scatter plots
- Views correlation graphs
- All output as base64-encoded SVG for embedding
"""

import base64
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


def _svg_encode(svg_content: str) -> str:
    """Encode SVG as base64 data URI."""
    encoded = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"


@dataclass
class ChartData:
    """Container for chart data and metadata."""
    chart_type: str
    title: str
    svg_content: str
    svg_data_uri: str
    width: int
    height: int
    
    def to_dict(self) -> dict:
        return {
            'chart_type': self.chart_type,
            'title': self.title,
            'svg_data_uri': self.svg_data_uri,
            'width': self.width,
            'height': self.height,
        }


class VisualReportGenerator:
    """
    Generates SVG visualizations for reports.
    
    Usage:
        generator = VisualReportGenerator()
        chart = generator.create_bar_chart(data, title)
    """
    
    # Color palette for charts
    COLORS = {
        'primary': '#3b82f6',    # Blue
        'secondary': '#8b5cf6',  # Purple
        'success': '#22c55e',    # Green
        'warning': '#f59e0b',    # Amber
        'danger': '#ef4444',     # Red
        'neutral': '#64748b',    # Slate
        'background': '#f8fafc',
        'text': '#1e293b',
        'grid': '#e2e8f0',
    }
    
    def __init__(self, default_width: int = 600, default_height: int = 300):
        self.default_width = default_width
        self.default_height = default_height
    
    def create_bar_chart(
        self,
        data: List[Dict],
        title: str,
        x_key: str = 'label',
        y_key: str = 'value',
        color: str = None,
        width: int = None,
        height: int = None,
    ) -> ChartData:
        """
        Create a horizontal bar chart.
        
        Args:
            data: List of dicts with x_key and y_key
            title: Chart title
            x_key: Key for labels
            y_key: Key for values
            color: Bar color (hex)
            width: Chart width
            height: Chart height
            
        Returns:
            ChartData with SVG
        """
        w = width or self.default_width
        h = height or self.default_height
        bar_color = color or self.COLORS['primary']
        
        if not data:
            return self._empty_chart(title, w, h, 'bar')
        
        # Calculate dimensions
        margin = {'top': 40, 'right': 20, 'bottom': 40, 'left': 120}
        inner_w = w - margin['left'] - margin['right']
        inner_h = h - margin['top'] - margin['bottom']
        
        max_value = max(d.get(y_key, 0) for d in data)
        if max_value == 0:
            max_value = 1
        
        bar_height = min(30, inner_h / len(data) * 0.7)
        bar_gap = (inner_h - bar_height * len(data)) / (len(data) + 1)
        
        # Build SVG
        bars_svg = []
        for i, item in enumerate(data):
            value = item.get(y_key, 0)
            label = str(item.get(x_key, ''))[:15]
            bar_width = (value / max_value) * inner_w
            y = margin['top'] + bar_gap + i * (bar_height + bar_gap)
            
            # Label
            bars_svg.append(f'''
                <text x="{margin['left'] - 10}" y="{y + bar_height/2 + 4}" 
                      text-anchor="end" font-size="12" fill="{self.COLORS['text']}">{label}</text>
            ''')
            
            # Bar
            bars_svg.append(f'''
                <rect x="{margin['left']}" y="{y}" width="{bar_width}" height="{bar_height}"
                      rx="4" fill="{bar_color}" opacity="0.9"/>
            ''')
            
            # Value label
            bars_svg.append(f'''
                <text x="{margin['left'] + bar_width + 8}" y="{y + bar_height/2 + 4}"
                      font-size="11" fill="{self.COLORS['neutral']}">{value:,.0f}</text>
            ''')
        
        svg_content = f'''
        <svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{w}" height="{h}" fill="{self.COLORS['background']}" rx="8"/>
            <text x="{w/2}" y="25" text-anchor="middle" font-size="14" 
                  font-weight="600" fill="{self.COLORS['text']}">{title}</text>
            {''.join(bars_svg)}
        </svg>
        '''
        
        return ChartData(
            chart_type='bar',
            title=title,
            svg_content=svg_content,
            svg_data_uri=_svg_encode(svg_content),
            width=w,
            height=h,
        )
    
    def create_donut_chart(
        self,
        data: List[Dict],
        title: str,
        value_key: str = 'value',
        label_key: str = 'label',
        colors: List[str] = None,
        width: int = None,
        height: int = None,
    ) -> ChartData:
        """
        Create a donut/pie chart.
        
        Args:
            data: List of dicts with values and labels
            title: Chart title
            
        Returns:
            ChartData with SVG
        """
        w = width or 300
        h = height or 300
        
        if not data:
            return self._empty_chart(title, w, h, 'donut')
        
        default_colors = [
            self.COLORS['primary'],
            self.COLORS['secondary'],
            self.COLORS['success'],
            self.COLORS['warning'],
            self.COLORS['danger'],
            self.COLORS['neutral'],
        ]
        chart_colors = colors or default_colors
        
        # Calculate total and percentages
        total = sum(d.get(value_key, 0) for d in data)
        if total == 0:
            total = 1
        
        cx, cy = w / 2, h / 2 - 20
        outer_r = min(w, h) / 2 - 40
        inner_r = outer_r * 0.6
        
        # Build arcs
        arcs_svg = []
        legend_svg = []
        current_angle = -90  # Start at top
        
        for i, item in enumerate(data):
            value = item.get(value_key, 0)
            label = str(item.get(label_key, ''))
            pct = value / total
            sweep_angle = pct * 360
            
            color = chart_colors[i % len(chart_colors)]
            
            # Calculate arc path
            start_rad = math.radians(current_angle)
            end_rad = math.radians(current_angle + sweep_angle)
            
            x1 = cx + outer_r * math.cos(start_rad)
            y1 = cy + outer_r * math.sin(start_rad)
            x2 = cx + outer_r * math.cos(end_rad)
            y2 = cy + outer_r * math.sin(end_rad)
            
            ix1 = cx + inner_r * math.cos(start_rad)
            iy1 = cy + inner_r * math.sin(start_rad)
            ix2 = cx + inner_r * math.cos(end_rad)
            iy2 = cy + inner_r * math.sin(end_rad)
            
            large_arc = 1 if sweep_angle > 180 else 0
            
            path = f"M {x1} {y1} A {outer_r} {outer_r} 0 {large_arc} 1 {x2} {y2} L {ix2} {iy2} A {inner_r} {inner_r} 0 {large_arc} 0 {ix1} {iy1} Z"
            
            arcs_svg.append(f'<path d="{path}" fill="{color}" opacity="0.9"/>')
            
            # Legend
            legend_y = h - 30 + (i // 3) * 18
            legend_x = 20 + (i % 3) * (w / 3)
            legend_svg.append(f'''
                <rect x="{legend_x}" y="{legend_y}" width="12" height="12" rx="2" fill="{color}"/>
                <text x="{legend_x + 16}" y="{legend_y + 10}" font-size="10" fill="{self.COLORS['text']}">{label[:10]} ({pct*100:.0f}%)</text>
            ''')
            
            current_angle += sweep_angle
        
        svg_content = f'''
        <svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{w}" height="{h}" fill="{self.COLORS['background']}" rx="8"/>
            <text x="{w/2}" y="25" text-anchor="middle" font-size="14"
                  font-weight="600" fill="{self.COLORS['text']}">{title}</text>
            {''.join(arcs_svg)}
            {''.join(legend_svg)}
        </svg>
        '''
        
        return ChartData(
            chart_type='donut',
            title=title,
            svg_content=svg_content,
            svg_data_uri=_svg_encode(svg_content),
            width=w,
            height=h,
        )
    
    def create_color_palette_chart(
        self,
        colors: List[str],
        title: str,
        labels: List[str] = None,
        width: int = None,
        height: int = None,
    ) -> ChartData:
        """
        Create a color palette visualization.
        
        Args:
            colors: List of hex colors
            title: Chart title
            labels: Optional labels for each color
            
        Returns:
            ChartData with SVG
        """
        w = width or 400
        h = height or 120
        
        if not colors:
            return self._empty_chart(title, w, h, 'palette')
        
        swatch_w = (w - 40) / len(colors)
        swatch_h = 60
        
        swatches_svg = []
        for i, color in enumerate(colors):
            x = 20 + i * swatch_w
            y = 40
            label = labels[i] if labels and i < len(labels) else color
            
            swatches_svg.append(f'''
                <rect x="{x}" y="{y}" width="{swatch_w - 4}" height="{swatch_h}" 
                      rx="6" fill="{color}" stroke="#e2e8f0" stroke-width="1"/>
                <text x="{x + swatch_w/2 - 2}" y="{y + swatch_h + 15}" 
                      text-anchor="middle" font-size="9" fill="{self.COLORS['neutral']}">{label[:8]}</text>
            ''')
        
        svg_content = f'''
        <svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{w}" height="{h}" fill="{self.COLORS['background']}" rx="8"/>
            <text x="{w/2}" y="25" text-anchor="middle" font-size="14"
                  font-weight="600" fill="{self.COLORS['text']}">{title}</text>
            {''.join(swatches_svg)}
        </svg>
        '''
        
        return ChartData(
            chart_type='palette',
            title=title,
            svg_content=svg_content,
            svg_data_uri=_svg_encode(svg_content),
            width=w,
            height=h,
        )
    
    def create_score_gauge(
        self,
        score: float,
        max_score: float = 100,
        title: str = "Score",
        width: int = None,
        height: int = None,
    ) -> ChartData:
        """
        Create a circular gauge for scores.
        
        Args:
            score: Current score value
            max_score: Maximum possible score
            title: Gauge title
            
        Returns:
            ChartData with SVG
        """
        w = width or 200
        h = height or 200
        
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 30
        stroke_width = 12
        
        pct = min(score / max_score, 1.0) if max_score > 0 else 0
        circumference = 2 * math.pi * r
        dash_offset = circumference * (1 - pct * 0.75)  # 270 degree arc
        
        # Color based on score
        if pct >= 0.7:
            color = self.COLORS['success']
        elif pct >= 0.4:
            color = self.COLORS['warning']
        else:
            color = self.COLORS['danger']
        
        svg_content = f'''
        <svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{w}" height="{h}" fill="{self.COLORS['background']}" rx="8"/>
            
            <!-- Background arc -->
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" 
                    stroke="{self.COLORS['grid']}" stroke-width="{stroke_width}"
                    stroke-dasharray="{circumference * 0.75} {circumference}"
                    stroke-linecap="round" transform="rotate(135 {cx} {cy})"/>
            
            <!-- Value arc -->
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                    stroke="{color}" stroke-width="{stroke_width}"
                    stroke-dasharray="{circumference * 0.75 * pct} {circumference}"
                    stroke-linecap="round" transform="rotate(135 {cx} {cy})"/>
            
            <!-- Score text -->
            <text x="{cx}" y="{cy + 5}" text-anchor="middle" 
                  font-size="28" font-weight="700" fill="{self.COLORS['text']}">{score:.0f}</text>
            <text x="{cx}" y="{cy + 25}" text-anchor="middle"
                  font-size="12" fill="{self.COLORS['neutral']}">{title}</text>
        </svg>
        '''
        
        return ChartData(
            chart_type='gauge',
            title=title,
            svg_content=svg_content,
            svg_data_uri=_svg_encode(svg_content),
            width=w,
            height=h,
        )
    
    def _empty_chart(self, title: str, width: int, height: int, chart_type: str) -> ChartData:
        """Create an empty chart placeholder."""
        svg_content = f'''
        <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{width}" height="{height}" fill="{self.COLORS['background']}" rx="8"/>
            <text x="{width/2}" y="25" text-anchor="middle" font-size="14"
                  font-weight="600" fill="{self.COLORS['text']}">{title}</text>
            <text x="{width/2}" y="{height/2}" text-anchor="middle"
                  font-size="12" fill="{self.COLORS['neutral']}">No data available</text>
        </svg>
        '''
        
        return ChartData(
            chart_type=chart_type,
            title=title,
            svg_content=svg_content,
            svg_data_uri=_svg_encode(svg_content),
            width=width,
            height=height,
        )


# === Quick test ===
if __name__ == "__main__":
    gen = VisualReportGenerator()
    
    # Test bar chart
    test_data = [
        {'label': 'Question', 'value': 45000},
        {'label': 'Statement', 'value': 38000},
        {'label': 'Story', 'value': 52000},
        {'label': 'Teaser', 'value': 41000},
    ]
    
    chart = gen.create_bar_chart(test_data, "Hook Pattern Performance")
    print(f"📊 Bar chart created: {len(chart.svg_content)} chars")
    
    # Test gauge
    gauge = gen.create_score_gauge(78, 100, "Hook Score")
    print(f"🎯 Gauge created: {len(gauge.svg_content)} chars")
    
    # Test palette
    palette = gen.create_color_palette_chart(
        ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b'],
        "Top Colors"
    )
    print(f"🎨 Palette created: {len(palette.svg_content)} chars")
