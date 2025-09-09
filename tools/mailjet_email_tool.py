import os
import json
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


class MailJetEmailTool:
    """
    A tool for sending emails using the MailJet API.
    
    This tool sends travel recommendation emails with HTML formatting.
    """
    
    def __init__(self):
        """Initialize the MailJet email tool with API credentials."""
        self.api_key = os.getenv("MAILJET_API_KEY")
        self.api_secret = os.getenv("MAILJET_API_SECRET")
        self.sender_email = os.getenv("SHARE_SENDER_EMAIL")
        self.sender_name = os.getenv("SHARE_SENDER_NAME", "Travel Agent App")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("MAILJET_API_KEY and MAILJET_API_SECRET must be set in environment variables")
        
        if not self.sender_email:
            raise ValueError("SHARE_SENDER_EMAIL must be set in environment variables")
        
        self.base_url = "https://api.mailjet.com/v3.1/send"
        
    def send_recommendation_email(
        self, 
        recipient_email: str,
        recommendation_data: Dict[str, Any],
        user_name: str = "Travel Enthusiast"
    ) -> Dict[str, Any]:
        """
        Send a travel recommendation email to the specified recipient.
        
        Args:
            recipient_email: Email address of the recipient
            recommendation_data: Dictionary containing the recommendation details
            user_name: Name of the user sharing the recommendation
            
        Returns:
            Dict containing the result of the email send operation
        """
        try:
            # Format the recommendation content
            html_content = self._format_recommendation_html(recommendation_data, user_name)
            text_content = self._format_recommendation_text(recommendation_data, user_name)
            
            # Prepare the email payload
            payload = {
                "Messages": [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [
                            {
                                "Email": recipient_email
                            }
                        ],
                        "Subject": f"🌍 Travel Recommendation from {user_name}",
                        "TextPart": text_content,
                        "HTMLPart": html_content
                    }
                ]
            }
            
            # Send the email via MailJet API
            response = requests.post(
                self.base_url,
                auth=(self.api_key, self.api_secret),
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message": f"Email sent successfully to {recipient_email}",
                    "mailjet_response": result
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to send email. Status: {response.status_code}",
                    "error_details": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Network error occurred: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Unexpected error occurred: {str(e)}"
            }
    
    def _format_recommendation_html(self, recommendation_data: Dict[str, Any], user_name: str) -> str:
        """Format the recommendation data into HTML email content."""
        
        # Extract key information
        title = recommendation_data.get("title", "Travel Recommendation")
        description = recommendation_data.get("description", "Check out this amazing travel plan!")
        full_recommendation = recommendation_data.get("full_recommendation", "")
        destination = recommendation_data.get("destination", "Unknown Destination")
        dates = recommendation_data.get("dates", "Dates not specified")
        budget = recommendation_data.get("budget", 0)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Travel Recommendation</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .trip-details {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .detail-item {{
                    margin: 10px 0;
                    padding: 8px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #495057;
                }}
                .recommendation-text {{
                    background: #e3f2fd;
                    padding: 20px;
                    border-left: 4px solid #2196f3;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .cta-button {{
                    display: inline-block;
                    background: #28a745;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✈️ Travel Recommendation</h1>
                <p>Shared by {user_name}</p>
            </div>
            
            <div class="content">
                <h2>🌍 {title}</h2>
                <p>{description}</p>
                
                <div class="trip-details">
                    <h3>📋 Trip Details</h3>
                    <div class="detail-item">
                        <span class="detail-label">🏖️ Destination:</span> {destination}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">📅 Travel Dates:</span> {dates}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">💰 Budget:</span> ${budget:,.0f}
                    </div>
                </div>
                
                <div class="recommendation-text">
                    <h3>🤖 AI-Powered Recommendation</h3>
                    <div style="white-space: pre-wrap;">{self._format_text_for_html(full_recommendation)}</div>
                </div>
                
                <div class="footer">
                    <p>This recommendation was generated using real-time data from:</p>
                    <p><strong>Amadeus Flight API • Booking.com Hotels • Anthropic Claude AI</strong></p>
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p style="margin-top: 20px; font-size: 12px;">
                        Powered by Travel Agent App with AI
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    def _format_text_for_html(self, text: str) -> str:
        """Format text content for proper HTML display."""
        if not text:
            return ""
        
        import html
        # Escape HTML characters
        formatted_text = html.escape(text)
        
        # Convert markdown-like formatting to HTML (basic support)
        import re
        # Handle bold text **text**
        formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)
        # Handle italic text *text* (but not already processed bold)
        formatted_text = re.sub(r'(?<!</strong>)\*([^*]+?)\*(?!<strong>)', r'<em>\1</em>', formatted_text)
        
        # Handle section headers (lines starting with emojis or special chars)
        lines = formatted_text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('<br>')
                continue
                
            # Check if line looks like a header (starts with emoji or special formatting)
            if any(char in line[:10] for char in ['🌴', '✈️', '🏨', '💰', '🗺️', '📋', '🤝']) and len(line) > 5:
                processed_lines.append(f'<h4 style="color: #2196f3; margin-top: 20px; margin-bottom: 10px;">{line}</h4>')
            elif line.startswith('- ') or line.startswith('• '):
                processed_lines.append(f'<li style="margin: 5px 0;">{line[2:]}</li>')
            elif line.startswith('1. ') or line.startswith('2. ') or any(line.startswith(f'{i}. ') for i in range(1, 10)):
                processed_lines.append(f'<li style="margin: 5px 0;">{line[3:]}</li>')
            else:
                processed_lines.append(f'<p style="margin: 8px 0;">{line}</p>')
        
        return '\n'.join(processed_lines)
    
    def _format_recommendation_text(self, recommendation_data: Dict[str, Any], user_name: str) -> str:
        """Format the recommendation data into plain text email content."""
        
        title = recommendation_data.get("title", "Travel Recommendation")
        destination = recommendation_data.get("destination", "Unknown Destination")
        dates = recommendation_data.get("dates", "Dates not specified")
        budget = recommendation_data.get("budget", 0)
        full_recommendation = recommendation_data.get("full_recommendation", "")
        
        text_content = f"""
✈️ TRAVEL RECOMMENDATION

Shared by: {user_name}

🌍 {title}

📋 TRIP DETAILS:
🏖️ Destination: {destination}
📅 Travel Dates: {dates}  
💰 Budget: ${budget:,.0f}

🤖 AI-POWERED RECOMMENDATION:
{full_recommendation}

---
This recommendation was generated using real-time data from:
Amadeus Flight API • Booking.com Hotels • Anthropic Claude AI

Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Powered by Travel Agent App with AI
        """
        return text_content


# Example usage
if __name__ == "__main__":
    # Test the email tool
    email_tool = MailJetEmailTool()
    
    # Sample recommendation data
    sample_recommendation = {
        "title": "🤖 AI-Powered Travel Plan for Paris",
        "description": "A fantastic trip to the City of Light!",
        "destination": "Paris",
        "dates": "2024-12-01 to 2024-12-08",
        "budget": 2500,
        "full_recommendation": "Paris offers incredible museums, world-class dining, and iconic landmarks. Consider visiting the Louvre, Eiffel Tower, and taking a Seine river cruise. The best time to visit is during spring or fall for pleasant weather."
    }
    
    # Send test email (replace with actual recipient)
    # result = email_tool.send_recommendation_email(
    #     recipient_email="test@example.com",
    #     recommendation_data=sample_recommendation,
    #     user_name="John Doe"
    # )
    # print(json.dumps(result, indent=2))