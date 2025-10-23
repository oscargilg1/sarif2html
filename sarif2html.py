#!/usr/bin/env python3
"""
SARIF to HTML Report Generator
Converts SARIF (Static Analysis Results Interchange Format) files to interactive HTML reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html


class SarifToHtmlConverter:
    def __init__(self, sarif_file):
        """Initialize converter with SARIF file path"""
        self.sarif_file = Path(sarif_file)
        self.data = None
        self.results = []
        self.notifications = []
        
    def load_sarif(self):
        """Load and parse SARIF JSON file"""
        try:
            with open(self.sarif_file, 'r') as f:
                self.data = json.load(f)
            
            # Extract results and notifications from first run
            if self.data.get('runs'):
                run = self.data['runs'][0]
                self.results = run.get('results', [])
                self.notifications = run.get('toolExecutionNotifications', [])
            
            print(f"✓ Loaded SARIF file: {self.sarif_file.name}")
            print(f"  - {len(self.results)} results found")
            print(f"  - {len(self.notifications)} notifications found")
            return True
        except Exception as e:
            print(f"✗ Error loading SARIF file: {e}", file=sys.stderr)
            return False
    
    def get_statistics(self):
        """Calculate statistics from results"""
        stats = {
            'total': len(self.results),
            'errors': 0,
            'warnings': 0,
            'notes': 0,
            'files': set(),
            'rules': set(),
            'by_level': defaultdict(int),
            'by_file': defaultdict(int),
        }
        
        for result in self.results:
            level = result.get('level', 'warning')
            stats['by_level'][level] += 1
            
            if level == 'error':
                stats['errors'] += 1
            elif level == 'warning':
                stats['warnings'] += 1
            elif level == 'note':
                stats['notes'] += 1
            
            # Collect unique files
            if result.get('locations'):
                uri = result['locations'][0].get('physicalLocation', {}).get('artifactLocation', {}).get('uri')
                if uri:
                    stats['files'].add(uri)
                    stats['by_file'][uri] += 1
            
            # Collect unique rules
            if result.get('ruleId'):
                stats['rules'].add(result['ruleId'])
        
        stats['files'] = len(stats['files'])
        stats['rules'] = len(stats['rules'])
        
        return stats
    
    def categorize_results(self):
        """Categorize results by severity level"""
        categorized = {'error': [], 'warning': [], 'note': []}
        for result in self.results:
            level = result.get('level', 'warning')
            if level not in categorized:
                categorized[level] = []
            categorized[level].append(result)
        return categorized
    
    def escape_html(self, text):
        """Escape HTML special characters"""
        if not text:
            return ''
        return html.escape(str(text))
    
    def get_location_info(self, result):
        """Extract location information from result"""
        try:
            location = result.get('locations', [{}])[0]
            physical = location.get('physicalLocation', {})
            artifact = physical.get('artifactLocation', {})
            region = physical.get('region', {})
            
            return {
                'file': artifact.get('uri', 'unknown'),
                'start_line': region.get('startLine', '?'),
                'start_column': region.get('startColumn', '?'),
                'end_line': region.get('endLine', '?'),
                'end_column': region.get('endColumn', '?'),
                'snippet': region.get('snippet', {}).get('text', ''),
            }
        except:
            return {
                'file': 'unknown',
                'start_line': '?',
                'start_column': '?',
                'end_line': '?',
                'end_column': '?',
                'snippet': '',
            }
    
    def generate_html(self, output_file=None):
        """Generate HTML report"""
        if output_file is None:
            output_file = self.sarif_file.stem + '_report.html'
        
        stats = self.get_statistics()
        categorized = self.categorize_results()
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SARIF Report - {self.escape_html(self.sarif_file.name)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .report-meta {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}

        .stat-card.error {{
            border-left-color: #e74c3c;
        }}

        .stat-card.warning {{
            border-left-color: #f39c12;
        }}

        .stat-card.note {{
            border-left-color: #3498db;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 0.5rem;
            color: #2c3e50;
        }}

        .stat-card.error .stat-value {{
            color: #e74c3c;
        }}

        .stat-card.warning .stat-value {{
            color: #f39c12;
        }}

        .stat-card.note .stat-value {{
            color: #3498db;
        }}

        .section {{
            margin-bottom: 2rem;
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .section-title.error {{
            border-bottom-color: #e74c3c;
        }}

        .section-title.warning {{
            border-bottom-color: #f39c12;
        }}

        .section-title.note {{
            border-bottom-color: #3498db;
        }}

        .severity-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .severity-badge.error {{
            background: #fadbd8;
            color: #c0392b;
        }}

        .severity-badge.warning {{
            background: #fdebd0;
            color: #b8860b;
        }}

        .severity-badge.note {{
            background: #d6eaf8;
            color: #1f618d;
        }}

        .result-item {{
            background: white;
            border: 1px solid #ecf0f1;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: all 0.2s;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}

        .result-item:hover {{
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-color: #bdc3c7;
        }}

        .result-header {{
            padding: 1.5rem;
            border-left: 4px solid #667eea;
            background: #f9f9f9;
        }}

        .result-item.error .result-header {{
            border-left-color: #e74c3c;
        }}

        .result-item.warning .result-header {{
            border-left-color: #f39c12;
        }}

        .result-item.note .result-header {{
            border-left-color: #3498db;
        }}

        .result-message {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.75rem;
        }}

        .result-rule {{
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            color: #7f8c8d;
            word-break: break-all;
        }}

        .result-body {{
            padding: 1.5rem;
        }}

        .result-section {{
            margin-bottom: 1.5rem;
        }}

        .result-section:last-child {{
            margin-bottom: 0;
        }}

        .result-section-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .result-section-content {{
            background: #f5f7fa;
            padding: 1rem;
            border-radius: 0.375rem;
            border-left: 3px solid #667eea;
        }}

        .result-item.error .result-section-content {{
            border-left-color: #e74c3c;
        }}

        .result-item.warning .result-section-content {{
            border-left-color: #f39c12;
        }}

        .result-item.note .result-section-content {{
            border-left-color: #3498db;
        }}

        .location-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}

        .location-item {{
            font-size: 0.9rem;
        }}

        .location-label {{
            font-weight: 600;
            color: #2c3e50;
        }}

        .location-value {{
            color: #7f8c8d;
            font-family: 'Courier New', monospace;
        }}

        .code-snippet {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1rem;
            border-radius: 0.375rem;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .tag {{
            background: #ecf0f1;
            color: #2c3e50;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.8rem;
            border: 1px solid #bdc3c7;
        }}

        .empty-state {{
            background: #f9f9f9;
            padding: 2rem;
            border-radius: 0.5rem;
            text-align: center;
            color: #7f8c8d;
        }}

        .notification-item {{
            background: #fef5e7;
            border: 1px solid #f39c12;
            border-left: 4px solid #f39c12;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0.375rem;
            color: #7d6608;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            background: white;
            border-radius: 0.375rem;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}

        th {{
            background: #f5f7fa;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid #ecf0f1;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: #f9f9f9;
        }}

        .file-name {{
            font-family: 'Courier New', monospace;
            color: #667eea;
            word-break: break-all;
        }}

        footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9rem;
        }}

        @media print {{
            body {{
                background: white;
            }}
            
            .result-item {{
                page-break-inside: avoid;
            }}
            
            header {{
                color: #2c3e50;
                background: #f5f7fa;
                border: 1px solid #bdc3c7;
            }}
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            header {{
                padding: 1.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}

            .location-info {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 SARIF Analysis Report</h1>
            <p>Static Analysis Results Interchange Format</p>
            <div class="report-meta">
                <p><strong>File:</strong> {self.escape_html(self.sarif_file.name)}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </header>

        <!-- Statistics Section -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Issues</div>
                <div class="stat-value">{stats['total']}</div>
            </div>
            <div class="stat-card error">
                <div class="stat-label">Errors</div>
                <div class="stat-value">{stats['errors']}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Warnings</div>
                <div class="stat-value">{stats['warnings']}</div>
            </div>
            <div class="stat-card note">
                <div class="stat-label">Notes</div>
                <div class="stat-value">{stats['notes']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Affected Files</div>
                <div class="stat-value">{stats['files']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique Rules</div>
                <div class="stat-value">{stats['rules']}</div>
            </div>
        </div>
"""
        
        # Add notifications section if any
        if self.notifications:
            html_content += f"""
        <!-- Notifications Section -->
        <div class="section">
            <div class="section-title warning">
                ⚠️ Build/Syntax Issues ({len(self.notifications)})
            </div>
            <div>
"""
            for notif in self.notifications:
                html_content += f"""
                <div class="notification-item">
                    {self.escape_html(notif.get('message', {}).get('text', ''))}
                </div>
"""
            html_content += """
            </div>
        </div>
"""
        
        # Add results by severity
        for level in ['error', 'warning', 'note']:
            results_by_level = categorized.get(level, [])
            if not results_by_level:
                continue
            
            level_title = level.upper()
            icon = '❌' if level == 'error' else '⚠️' if level == 'warning' else 'ℹ️'
            
            html_content += f"""
        <!-- {level_title} Section -->
        <div class="section">
            <div class="section-title {level}">
                {icon} {level_title}s ({len(results_by_level)})
            </div>
"""
            
            for idx, result in enumerate(results_by_level, 1):
                loc_info = self.get_location_info(result)
                rule_id = result.get('ruleId', 'unknown')
                message = result.get('message', {}).get('text', '')
                tags = result.get('properties', {}).get('tags', [])
                
                html_content += f"""
            <div class="result-item {level}">
                <div class="result-header">
                    <div class="result-message">
                        {self.escape_html(message)}
                    </div>
                    <div class="result-rule">
                        Rule: {self.escape_html(rule_id)}
                    </div>
                </div>
                <div class="result-body">
"""
                
                # Location information
                html_content += f"""
                    <div class="result-section">
                        <div class="result-section-title">📍 Location</div>
                        <div class="result-section-content">
                            <div class="location-info">
                                <div class="location-item">
                                    <div class="location-label">File:</div>
                                    <div class="location-value file-name">{self.escape_html(loc_info['file'])}</div>
                                </div>
                                <div class="location-item">
                                    <div class="location-label">Line:</div>
                                    <div class="location-value">{loc_info['start_line']}</div>
                                </div>
                                <div class="location-item">
                                    <div class="location-label">Column:</div>
                                    <div class="location-value">{loc_info['start_column']}</div>
                                </div>
                            </div>
                        </div>
                    </div>
"""
                
                # Code snippet
                if loc_info['snippet']:
                    html_content += f"""
                    <div class="result-section">
                        <div class="result-section-title">💻 Code</div>
                        <div class="code-snippet">{self.escape_html(loc_info['snippet'])}</div>
                    </div>
"""
                
                # Tags
                if tags:
                    html_content += f"""
                    <div class="result-section">
                        <div class="result-section-title">🏷️ Tags</div>
                        <div class="tags">
"""
                    for tag in tags:
                        html_content += f'                            <span class="tag">{self.escape_html(tag)}</span>\n'
                    html_content += """
                        </div>
                    </div>
"""
                
                html_content += """
                </div>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        # Add file summary table
        if stats['by_file']:
            html_content += f"""
        <!-- File Summary -->
        <div class="section">
            <div class="section-title">
                📁 Issues by File
            </div>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th style="text-align: right;">Count</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for file, count in sorted(stats['by_file'].items(), key=lambda x: x[1], reverse=True):
                html_content += f"""
                    <tr>
                        <td class="file-name">{self.escape_html(file)}</td>
                        <td style="text-align: right;"><strong>{count}</strong></td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""
        
        # Footer
        html_content += """
        <footer>
            <p>Generated by SARIF to HTML Converter</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # Write to file
        try:
            with open(output_file, 'w') as f:
                f.write(html_content)
            print(f"✓ HTML report generated: {output_file}")
            return output_file
        except Exception as e:
            print(f"✗ Error writing HTML file: {e}", file=sys.stderr)
            return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python sarif-to-html.py <sarif_file> [output_file]")
        print("\nExample:")
        print("  python sarif-to-html.py report.sarif")
        print("  python sarif-to-html.py report.sarif output_report.html")
        sys.exit(1)
    
    sarif_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = SarifToHtmlConverter(sarif_file)
    
    if not converter.load_sarif():
        sys.exit(1)
    
    html_file = converter.generate_html(output_file)
    
    if html_file:
        print(f"\n✓ Done! Open '{html_file}' in your browser to view the report.")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
