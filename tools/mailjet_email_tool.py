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
        
        # Handle different data structures - try multiple sources for the recommendation text
        full_recommendation = ""
        if isinstance(recommendation_data, dict):
            # First try the standard keys
            if recommendation_data.get("full_recommendation"):
                full_recommendation = recommendation_data.get("full_recommendation")
                
                # Check if full_recommendation is actually a stringified dict
                if isinstance(full_recommendation, str) and full_recommendation.strip().startswith('{'):
                    print("📧 full_recommendation is a stringified dict, parsing...")
                    try:
                        import ast
                        parsed_full_rec = ast.literal_eval(full_recommendation)
                        if isinstance(parsed_full_rec, dict) and parsed_full_rec.get('raw'):
                            full_recommendation = parsed_full_rec.get('raw')
                            print(f"📧 Extracted from parsed full_recommendation['raw'], length: {len(full_recommendation)}")
                    except Exception as e:
                        print(f"📧 Failed to parse full_recommendation: {e}")
                        
            elif recommendation_data.get("raw"):
                full_recommendation = recommendation_data.get("raw")
            elif recommendation_data.get("description"):
                full_recommendation = recommendation_data.get("description")
            else:
                # If it's a dict with unknown structure, try to find text content
                full_recommendation = str(recommendation_data)
        else:
            full_recommendation = str(recommendation_data)
        
        destination = recommendation_data.get("destination", "Unknown Destination")
        dates = recommendation_data.get("dates", "Dates not specified")
        budget = recommendation_data.get("budget", 0)
        
        print(f"📧 Email data type: {type(recommendation_data)}")
        print(f"📧 Email data keys: {list(recommendation_data.keys()) if isinstance(recommendation_data, dict) else 'Not a dict'}")
        print(f"📧 Raw data preview: {repr(recommendation_data)[:200]}...")
        
        # If we got a string that looks like a dictionary, try to parse it
        if isinstance(recommendation_data, str) and recommendation_data.strip().startswith('{'):
            try:
                import ast
                print("📧 Attempting to parse string as dictionary...")
                parsed_data = ast.literal_eval(recommendation_data)
                if isinstance(parsed_data, dict):
                    print(f"📧 Successfully parsed! Keys: {list(parsed_data.keys())}")
                    recommendation_data = parsed_data
                    # Re-extract with the parsed data
                    if parsed_data.get("full_recommendation"):
                        full_recommendation = parsed_data.get("full_recommendation")
                    elif parsed_data.get("raw"):
                        full_recommendation = parsed_data.get("raw")
                        print(f"📧 Using 'raw' key, length: {len(full_recommendation)}")
                    elif parsed_data.get("description"):
                        full_recommendation = parsed_data.get("description")
                    else:
                        full_recommendation = str(parsed_data)
            except Exception as e:
                print(f"📧 Failed to parse string as dict: {e}")
        
        print(f"📧 Final recommendation length: {len(str(full_recommendation))}")
        print(f"📧 Final recommendation preview: {repr(str(full_recommendation)[:100])}...")
        
        # Format the recommendation text for HTML
        formatted_recommendation = self._format_text_for_html(full_recommendation)
        
        # Debug: Print what we're formatting
        print(f"📧 DEBUG - Original text length: {len(full_recommendation)}")
        print(f"📧 DEBUG - Original text preview: {full_recommendation[:200]}...")
        print(f"📧 DEBUG - Formatted HTML length: {len(formatted_recommendation)}")
        print(f"📧 DEBUG - Formatted HTML preview: {formatted_recommendation[:300]}...")
        
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
                    <div>{formatted_recommendation}</div>
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
            return "<p style='color: red;'>No recommendation available.</p>"
        
        import html
        import re
        
        # Convert to string and escape HTML
        text = str(text)
        print(f"📧 STEP 1 - Raw text: {repr(text[:100])}...")
        
        # Escape HTML characters
        formatted_text = html.escape(text)
        print(f"📧 STEP 2 - After HTML escape: {repr(formatted_text[:100])}...")
        
        # Simple approach: just convert line breaks to <br> and add basic styling
        formatted_text = formatted_text.replace('\n\n', '</p><p style="margin: 15px 0; line-height: 1.6;">')
        formatted_text = formatted_text.replace('\n', '<br>')
        
        # Convert **bold** text
        formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #2c3e50;">\1</strong>', formatted_text)
        
        # Wrap in paragraph tags
        if not formatted_text.startswith('<p'):
            formatted_text = f'<p style="margin: 15px 0; line-height: 1.6;">{formatted_text}</p>'
        
        # Basic header detection - simpler approach
        formatted_text = re.sub(
            r'<p([^>]*)>([🌴✈️🏨💰🗺️📋🤝📅🎯🎨🔥⚙️][^<]*)</p>',
            r'<h3 style="color: #3498db; margin: 25px 0 15px 0; font-size: 20px; border-bottom: 2px solid #3498db; padding-bottom: 10px;">\2</h3>',
            formatted_text
        )
        
        result = f'''
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    color: #2c3e50; 
                    line-height: 1.6; 
                    max-width: 800px; 
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;">
            {formatted_text}
        </div>
        '''
        
        print(f"📧 STEP 3 - Final HTML: {repr(result[:200])}...")
        return result
    
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