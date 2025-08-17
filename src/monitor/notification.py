import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# Configuration
NOTIFICATION_CONFIG = {
    'email': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': os.getenv('EMAIL_SENDER', 'iyed.guizeni2002@gmail.com'),  # Replace with your email
        'sender_password': os.getenv('EMAIL_PASSWORD', 'rhwy evct qibx pcsf'),   # Replace with your app password
        'recipients': os.getenv('EMAIL_RECIPIENTS', 'guizeniiyed@isimsf.u-sfax.tn').split(',')
    },
    'slack': {
        'webhook_url': os.getenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'),  # Replace with your webhook
        'channel': os.getenv('SLACK_CHANNEL', '#ml-alerts'),
        'username': 'ML-Monitor-Bot'
    }
}

def send_email(message, severity='CRITICAL'):
    """Send email notification for ML alerts"""
    try:
        config = NOTIFICATION_CONFIG['email']
        
        # Skip if no proper email configuration
        if 'your_email@gmail.com' in config['sender_email']:
            print("  Email not configured - skipping email notification")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(config['recipients'])
        msg['Subject'] = f" ML Alert - {severity}: Prediction Drift Detected"
        
        # Create HTML version
        html_message = create_html_email(message, severity)
        msg.attach(MIMEText(html_message, 'html'))
        
        # Send email
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['sender_email'], config['sender_password'])
        server.send_message(msg)
        server.quit()
        
        print(" Email notification sent successfully")
        return True
        
    except Exception as e:
        print(f" Email notification failed: {e}")
        return False

def send_slack_message(message, severity='CRITICAL'):
    """Send Slack notification for ML alerts"""
    try:
        config = NOTIFICATION_CONFIG['slack']
        
        # Skip if no proper Slack configuration
        if 'YOUR/SLACK/WEBHOOK' in config['webhook_url']:
            print("  Slack not configured - skipping Slack notification")
            return False
        
        # Create Slack payload
        color = "danger" if severity == 'CRITICAL' else "warning"
        #emoji = "" if severity == 'CRITICAL' else ""
        
        # Truncate message for Slack (max 7000 characters)
        truncated_message = message[:6000] + "..." if len(message) > 6000 else message
        
        payload = {
            "channel": config['channel'],
            "username": config['username'],
            "icon_emoji": ":robot_face:",
            "attachments": [
                {
                    "color": color,
                    "text": f"```{truncated_message}```",
                    "fields": [
                        {
                            "title": "Severity",
                            "value": severity,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        },
                        {
                            "title": "System",
                            "value": "Lead Scoring Model",
                            "short": True
                        }
                    ],
                    "footer": "ML Monitoring System",
                    "ts": int(datetime.now().timestamp()),
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Dashboard",
                            "url": "http://monitoring-dashboard.company.com"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(config['webhook_url'], json=payload, timeout=10)
        response.raise_for_status()
        
        print(" Slack notification sent successfully")
        return True
        
    except Exception as e:
        print(f" Slack notification failed: {e}")
        return False

def format_alert_message_html(message):
    """Format alert message for better HTML display"""
    # Split message into sections
    sections = message.split('\n\n')
    formatted_html = ""
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split('\n')
        first_line = lines[0].strip()
        
        # Handle different sections
        if "BATCH DETAILS:" in first_line:
            formatted_html += format_batch_details(lines)
        elif "ALERT SUMMARY:" in first_line:
            formatted_html += format_alert_summary(lines)
        elif "CRITICAL ISSUES" in first_line:
            formatted_html += format_critical_issues(lines)
        elif "WARNING ISSUES" in first_line:
            formatted_html += format_warning_issues(lines)
        elif "PRIORITY ACTIONS:" in first_line:
            formatted_html += format_priority_actions(lines)
        elif "ESCALATION CONTACT:" in first_line:
            formatted_html += format_contact_info(lines)
        else:
            # Default formatting for other sections
            formatted_html += f"<div class='alert-section'>{section}</div>"
    
    return formatted_html

def format_batch_details(lines):
    """Format batch details section"""
    html = '<div class="batch-details">'
    html += '<h3> Batch Details</h3>'
    html += '<div class="detail-grid">'
    
    for line in lines[1:]:  # Skip header
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip().replace('  ', '')
            value = parts[1].strip()
            html += f'''
            <div class="detail-item">
                <span class="detail-label">{label}:</span>
                <span class="detail-value">{value}</span>
            </div>
            '''
    
    html += '</div></div>'
    return html

def format_alert_summary(lines):
    """Format alert summary section"""
    html = '<div class="alert-section">'
    html += '<h3> Alert Summary</h3>'
    html += '<div class="detail-grid">'
    
    for line in lines[1:]:  # Skip header
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip().replace('  ', '')
            value = parts[1].strip()
            html += f'''
            <div class="detail-item">
                <span class="detail-label">{label}:</span>
                <span class="detail-value">{value}</span>
            </div>
            '''
    
    html += '</div></div>'
    return html

def format_critical_issues(lines):
    """Format critical issues section"""
    html = '<div class="alert-section">'
    html += '<h3> Critical Issues (Immediate Action Required)</h3>'
    
    current_item = ""
    for line in lines[2:]:  # Skip header and separator
        if line.strip() and not line.startswith('   '):
            # New alert item
            if current_item:
                html += format_alert_item(current_item)
            current_item = line
        else:
            # Add to current item
            current_item += '\n' + line
    
    # Add last item
    if current_item:
        html += format_alert_item(current_item)
    
    html += '</div>'
    return html

def format_warning_issues(lines):
    """Format warning issues section"""
    html = '<div class="alert-section">'
    html += '<h3> Warning Issues (Monitor Closely)</h3>'
    
    current_item = ""
    for line in lines[2:]:  # Skip header and separator
        if line.strip() and not line.startswith('   '):
            # New alert item
            if current_item:
                html += format_alert_item(current_item)
            current_item = line
        else:
            # Add to current item
            current_item += '\n' + line
    
    # Add last item
    if current_item:
        html += format_alert_item(current_item)
    
    html += '</div>'
    return html

def format_alert_item(item_text):
    """Format individual alert item"""
    lines = item_text.split('\n')
    html = '<div class="alert-item">'
    
    # First line is the metric
    metric_line = lines[0].strip()
    if ':' in metric_line:
        parts = metric_line.split(':', 1)
        metric_name = parts[0].strip().replace('1. ', '').replace('2. ', '').replace('3. ', '')
        metric_details = parts[1].strip()
        
        html += f'<div class="metric-name">{metric_name}</div>'
        html += f'<div class="metric-value">{metric_details}</div>'
    
    # Process other lines
    for line in lines[1:]:
        line = line.strip()
        if 'Business Impact:' in line:
            impact = line.replace('Business Impact:', '').strip()
            html += f'<div class="business-impact"><strong> Business Impact:</strong> {impact}</div>'
        elif 'Recommended Action:' in line:
            action = line.replace(' Recommended Action:', '').strip()
            html += f'<div class="recommended-action"><strong> Recommended Action:</strong> {action}</div>'
    
    html += '</div>'
    return html

def format_priority_actions(lines):
    """Format priority actions section"""
    html = '<div class="priority-actions">'
    html += '<h3> Priority Actions</h3>'
    html += '<ul>'
    
    current_item = ""
    for line in lines[2:]:  # Skip header and separator
        if line.strip():
            if line.startswith('   '):
                # Sub-item
                current_item += line + '\n'
            else:
                # New main item
                if current_item:
                    html += f'<li>{current_item.strip()}</li>'
                current_item = line.strip()
    
    # Add last item
    if current_item:
        html += f'<li>{current_item.strip()}</li>'
    
    html += '</ul></div>'
    return html

def format_contact_info(lines):
    """Format contact information section"""
    html = '<div class="contact-info">'
    html += '<h3> Escalation Contact</h3>'
    html += '<div class="detail-grid">'
    
    for line in lines[1:]:  # Skip header
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip().replace('   ', '')
            value = parts[1].strip()
            html += f'''
            <div class="detail-item">
                <span class="detail-label">{label}:</span>
                <span class="detail-value">{value}</span>
            </div>
            '''
    
    html += '</div></div>'
    return html

def create_html_email(message, severity):
    """Create HTML email template"""
    color = "#FF0000" if severity == 'CRITICAL' else "#FFA500"
    bg_color = "#FFE6E6" if severity == 'CRITICAL' else "#FFF4E6"
    
    # Format the message for better display
    formatted_message = format_alert_message_html(message)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background-color: #f4f4f4; 
            }}
            .container {{ 
                max-width: 700px; 
                margin: 0 auto; 
                background-color: white; 
                box-shadow: 0 0 10px rgba(0,0,0,0.1); 
            }}
            .header {{ 
                background-color: {color}; 
                color: white; 
                padding: 20px; 
                text-align: center; 
            }}
            .content {{ 
                padding: 20px; 
                line-height: 1.6; 
            }}
            .footer {{ 
                background-color: #333; 
                color: white; 
                padding: 15px; 
                text-align: center; 
                font-size: 12px; 
            }}
            .message-box {{ 
                background-color: {bg_color}; 
                padding: 20px; 
                margin: 20px 0; 
                border-left: 4px solid {color}; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                white-space: pre-wrap; 
                font-size: 13px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                line-height: 1.5;
            }}
            .alert-section {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }}
            .alert-item {{
                margin: 15px 0;
                padding: 12px;
                background-color: white;
                border-radius: 6px;
                border-left: 3px solid {color};
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .metric-name {{
                font-weight: bold;
                color: {color};
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .metric-value {{
                font-family: 'Consolas', monospace;
                background-color: #f1f3f4;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                display: inline-block;
                margin: 0 5px;
            }}
            .business-impact {{
                color: #d73027;
                font-style: italic;
                margin: 8px 0;
                padding: 8px;
                background-color: #fdf2f2;
                border-radius: 4px;
                border-left: 2px solid #d73027;
            }}
            .recommended-action {{
                color: #2e7d32;
                margin: 8px 0;
                padding: 8px;
                background-color: #f1f8e9;
                border-radius: 4px;
                border-left: 2px solid #4caf50;
            }}
            .batch-details {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #bbdefb;
                margin: 15px 0;
            }}
            .batch-details h3 {{
                color: #1565c0;
                margin-top: 0;
                margin-bottom: 10px;
            }}
            .detail-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin: 10px 0;
            }}
            .detail-item {{
                padding: 8px;
                background-color: white;
                border-radius: 4px;
                border: 1px solid #e0e0e0;
            }}
            .detail-label {{
                font-weight: bold;
                color: #424242;
                display: block;
                margin-bottom: 3px;
            }}
            .detail-value {{
                color: #666;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }}
            .priority-actions {{
                background-color: #fff3e0;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ffcc02;
                margin: 20px 0;
            }}
            .priority-actions h3 {{
                color: #f57c00;
                margin-top: 0;
            }}
            .contact-info {{
                background-color: #f3e5f5;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ce93d8;
                margin: 20px 0;
            }}
            .contact-info h3 {{
                color: #7b1fa2;
                margin-top: 0;
            }}
            .severity-badge {{
                background-color: {color};
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }}
            .action-btn {{ 
                background-color: {color}; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block; 
                margin: 15px 0; 
                font-weight: bold;
            }}
            .action-btn:hover {{
                opacity: 0.8;
            }}
            .urgent-box {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                margin: 15px 0;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 ML Model Alert</h1>
                <div class="severity-badge">{severity}</div>
                <p>Prediction Drift Detection System</p>
            </div>
            <div class="content">
                {formatted_message}
                
                {create_urgent_section(severity)}
                
                <h3>📋 Next Steps:</h3>
                <ul>
                    <li><strong>Immediate:</strong> Review model performance metrics</li>
                    <li><strong>Investigate:</strong> Check data pipeline for issues</li>
                    <li><strong>Analyze:</strong> Investigate root cause of drift</li>
                    <li><strong>Decide:</strong> Consider model retraining if necessary</li>
                </ul>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="http://monitoring-dashboard.company.com" class="action-btn">📊 View Monitoring Dashboard</a>
                </div>
            </div>
            <div class="footer">
                <p><strong>ML Monitoring System</strong> | Lead Scoring Model</p>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>For support, contact: ml-team@company.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def create_urgent_section(severity):
    """Create urgent action section for HTML email"""
    if severity == 'CRITICAL':
        return """
        <div class="urgent-box">
            <h3>🔥 URGENT ACTION REQUIRED</h3>
            <p><strong>This is a CRITICAL alert</strong> - immediate attention needed!</p>
            <ul>
                <li>Model predictions may be unreliable</li>
                <li>Business impact possible</li>
                <li>Escalate to on-call team if needed</li>
            </ul>
        </div>
        """
    else:
        return """
        <div class="urgent-box">
            <h3>⚠️ MONITORING ALERT</h3>
            <p><strong>Warning level alert</strong> - please review when possible.</p>
            <ul>
                <li>Monitor trend closely</li>
                <li>Prepare for potential action</li>
                <li>Document observations</li>
            </ul>
        </div>
        """

def send_notifications(message, severity='CRITICAL'):
    """Send notifications through configured channels"""
    print(f"\n📧 Sending {severity} notifications...")
    
    # Send through all configured channels
    results = {
        'email': send_email(message, severity),
        'slack': send_slack_message(message, severity)
    }
    
    # Calculate success rate
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"✅ Notifications sent: {success_count}/{total_count} successful")
    
    # Log results
    for channel, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {channel.upper()}: {status}")
    
    return results

def test_notifications():
    """Test email and Slack notifications"""
    
    print("🧪 TESTING NOTIFICATION SYSTEM")
    print("=" * 50)
    
    # Test message
    test_message = """🚨 CRITICAL DRIFT DETECTED 🚨
==================================================
📊 BATCH DETAILS:
  Model Version: 20250708_202407
  Batch Size: 100 predictions
  Timestamp: 2025-07-15T14:30:22.123456
  Output File: prediction_v20250708_202407.csv

⚠️  ALERT SUMMARY:
  Total Alerts: 2
  Critical: 2
  Warning: 0

🔥 CRITICAL ISSUES (Immediate Action Required):
---------------------------------------------
1. mean_drift_zscore: 3.125 (threshold: 2.5)
   📈 Business Impact: Significant probability shift - leads may be misclassified
   🎯 Recommended Action: URGENT: Stop using current model predictions.

2. p90_shift: 0.284 (threshold: 0.25)
   📈 Business Impact: Top 10% predictions severely shifted - missing best leads?
   🎯 Recommended Action: URGENT: Emergency response required.

🎯 PRIORITY ACTIONS:
--------------------
1. 🔍 INVESTIGATE IMMEDIATELY:
   - Check data pipeline for errors
   - Verify feature engineering process
   - Review recent data sources

📞 ESCALATION CONTACT:
   ML Team: ml-team@company.com
   Data Engineering: data-eng@company.com
   On-Call: on-call@company.com
"""
    
    # Test notifications
    print("\n🚀 Testing CRITICAL alert...")
    results = send_notifications(test_message, 'CRITICAL')
    
    print(f"\n📊 Test Results:")
    print(f"  Email: {'✅ Sent' if results['email'] else '❌ Failed'}")
    print(f"  Slack: {'✅ Sent' if results['slack'] else '❌ Failed'}")
    
    if not any(results.values()):
        print(f"\n⚠️  No notifications sent - check configuration:")
        print(f"  1. Update EMAIL_SENDER and EMAIL_PASSWORD environment variables")
        print(f"  2. Update SLACK_WEBHOOK_URL environment variable")
        print(f"  3. Or edit NOTIFICATION_CONFIG in notification.py directly")
    
    return results

if __name__ == "__main__":
    test_notifications()