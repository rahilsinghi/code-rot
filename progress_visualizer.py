#!/usr/bin/env python3
"""
Progress Visualizer Module
Enhanced visualization and analytics for coding practice progress
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from collections import defaultdict, Counter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("📊 Matplotlib not available. Install with: pip install matplotlib")

class ProgressVisualizer:
    def __init__(self, db_path="practice_data/practice.db"):
        self.db_path = db_path
        
    def generate_progress_report(self, days=30, language="python"):
        """Generate comprehensive progress report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT pr.problem_id) as completed_problems,
                AVG(pr.time_spent) as avg_time,
                COUNT(CASE WHEN p.difficulty = 'easy' THEN 1 END) as easy_count,
                COUNT(CASE WHEN p.difficulty = 'medium' THEN 1 END) as medium_count,
                COUNT(CASE WHEN p.difficulty = 'hard' THEN 1 END) as hard_count
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
        '''.format(days), (language,))
        
        stats = cursor.fetchone()
        
        # Get daily progress
        cursor.execute('''
            SELECT DATE(pr.completed_at) as date, COUNT(*) as count
            FROM progress pr
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            GROUP BY DATE(pr.completed_at)
            ORDER BY date
        '''.format(days), (language,))
        
        daily_progress = cursor.fetchall()
        
        # Get topic distribution
        cursor.execute('''
            SELECT p.topic, COUNT(*) as count
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            GROUP BY p.topic
            ORDER BY count DESC
        '''.format(days), (language,))
        
        topic_distribution = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = {
            'period': f"Last {days} days",
            'language': language,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_completed': stats[0] or 0,
                'avg_time_minutes': round(stats[1] or 0, 1),
                'difficulty_breakdown': {
                    'easy': stats[2] or 0,
                    'medium': stats[3] or 0,
                    'hard': stats[4] or 0
                }
            },
            'daily_progress': [{'date': date, 'count': count} for date, count in daily_progress],
            'topic_distribution': [{'topic': topic, 'count': count} for topic, count in topic_distribution]
        }
        
        return report
    
    def create_progress_charts(self, days=30, language="python", output_dir="practice_data/charts"):
        """Create visual charts for progress"""
        if not MATPLOTLIB_AVAILABLE:
            print("❌ Matplotlib not available. Cannot create charts.")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        report = self.generate_progress_report(days, language)
        
        # 1. Daily Progress Chart
        if report['daily_progress']:
            dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in report['daily_progress']]
            counts = [item['count'] for item in report['daily_progress']]
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates, counts, marker='o', linewidth=2, markersize=6)
            plt.title(f'Daily Problem Solving Progress - {language.title()}', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Problems Solved', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_path = os.path.join(output_dir, f'daily_progress_{language}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"📊 Daily progress chart saved: {chart_path}")
        
        # 2. Difficulty Distribution Pie Chart
        difficulty_data = report['summary']['difficulty_breakdown']
        if any(difficulty_data.values()):
            labels = [k.title() for k, v in difficulty_data.items() if v > 0]
            sizes = [v for v in difficulty_data.values() if v > 0]
            colors = ['#90EE90', '#FFD700', '#FF6B6B'][:len(labels)]
            
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title(f'Problem Difficulty Distribution - {language.title()}', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            chart_path = os.path.join(output_dir, f'difficulty_distribution_{language}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"📊 Difficulty distribution chart saved: {chart_path}")
        
        # 3. Topic Distribution Bar Chart
        if report['topic_distribution']:
            topics = [item['topic'].title() for item in report['topic_distribution'][:10]]  # Top 10
            counts = [item['count'] for item in report['topic_distribution'][:10]]
            
            plt.figure(figsize=(12, 8))
            bars = plt.bar(topics, counts, color='skyblue', alpha=0.7)
            plt.title(f'Top Topics Practiced - {language.title()}', fontsize=16, fontweight='bold')
            plt.xlabel('Topic', fontsize=12)
            plt.ylabel('Problems Solved', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            chart_path = os.path.join(output_dir, f'topic_distribution_{language}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"📊 Topic distribution chart saved: {chart_path}")
        
        return True
    
    def print_progress_summary(self, days=30, language="python"):
        """Print a beautiful text-based progress summary"""
        report = self.generate_progress_report(days, language)
        
        print(f"\n{'='*60}")
        print(f"📈 PROGRESS REPORT - {report['period'].upper()}")
        print(f"{'='*60}")
        print(f"🔤 Language: {language.title()}")
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary stats
        summary = report['summary']
        print(f"\n📊 SUMMARY STATISTICS")
        print(f"   ✅ Total Problems Solved: {summary['total_completed']}")
        print(f"   ⏱️  Average Time per Problem: {summary['avg_time_minutes']} minutes")
        
        # Difficulty breakdown
        diff = summary['difficulty_breakdown']
        print(f"\n🎯 DIFFICULTY BREAKDOWN")
        print(f"   🟢 Easy: {diff['easy']} problems")
        print(f"   🟡 Medium: {diff['medium']} problems") 
        print(f"   🔴 Hard: {diff['hard']} problems")
        
        # Recent activity
        if report['daily_progress']:
            recent_days = report['daily_progress'][-7:]  # Last 7 days
            total_recent = sum(item['count'] for item in recent_days)
            print(f"\n🔥 RECENT ACTIVITY (Last 7 days)")
            print(f"   📈 Problems Solved: {total_recent}")
            print(f"   📊 Daily Average: {total_recent/7:.1f}")
        
        # Top topics
        if report['topic_distribution']:
            print(f"\n🏆 TOP TOPICS")
            for i, item in enumerate(report['topic_distribution'][:5], 1):
                print(f"   {i}. {item['topic'].title()}: {item['count']} problems")
        
        # Performance insights
        self._print_insights(report)
        
        print(f"\n{'='*60}")
    
    def _print_insights(self, report):
        """Generate and print performance insights"""
        print(f"\n💡 INSIGHTS & RECOMMENDATIONS")
        
        summary = report['summary']
        total = summary['total_completed']
        
        if total == 0:
            print("   🚀 Start your coding journey! Try solving your first problem.")
            return
        
        # Difficulty analysis
        diff = summary['difficulty_breakdown']
        easy_pct = (diff['easy'] / total) * 100 if total > 0 else 0
        medium_pct = (diff['medium'] / total) * 100 if total > 0 else 0
        hard_pct = (diff['hard'] / total) * 100 if total > 0 else 0
        
        if easy_pct > 70:
            print("   📈 Consider tackling more medium/hard problems to challenge yourself!")
        elif hard_pct > 50:
            print("   🎯 Great job on hard problems! Balance with easier ones for confidence.")
        elif medium_pct > 60:
            print("   ⚖️  Nice balance! Try mixing in more easy and hard problems.")
        
        # Topic diversity
        topics = len(report['topic_distribution'])
        if topics < 3:
            print("   🌟 Try exploring more topics to broaden your skills!")
        elif topics > 8:
            print("   🎨 Great topic diversity! Consider deepening knowledge in key areas.")
        
        # Consistency
        if report['daily_progress']:
            days_active = len(report['daily_progress'])
            if days_active < 5:
                print("   📅 Try to practice more consistently for better retention!")
            elif days_active > 20:
                print("   🔥 Excellent consistency! Keep up the great work!")
    
    def export_report(self, days=30, language="python", output_file=None):
        """Export detailed report to JSON"""
        report = self.generate_progress_report(days, language)
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"practice_data/reports/progress_report_{language}_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Progress report exported to: {output_file}")
        return output_file

if __name__ == "__main__":
    visualizer = ProgressVisualizer()
    
    # Print summary
    visualizer.print_progress_summary(30, "python")
    
    # Create charts if matplotlib is available
    if MATPLOTLIB_AVAILABLE:
        visualizer.create_progress_charts(30, "python")
    
    # Export report
    visualizer.export_report(30, "python") 