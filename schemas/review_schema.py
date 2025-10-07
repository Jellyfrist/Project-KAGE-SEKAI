from litellm import completion
from config import MODEL
import json

review_schema = {
  "name": "MultiAspectReview",
  "schema": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "string",
        "description": "Reference ID of the product analysed."
      },
      "product_name": {
        "type": "string",
        "description": "Name of the product mentioned in the review."
      },
      "review_text": {
        "type": "string",
        "description": "Raw review text written by the user."
      },
      "aspects": {
        "type": "array",
        "description": "List of aspects analysed for this review.",
        "items": {
          "type": "object",
          "properties": {
            "aspect_name": {
              "type": "string",
              "description": "Aspect being evaluated (e.g., 'คุณภาพ', 'ราคา', 'บริการ')."
            },
            "sentiment": {
              "type": "string",
              "enum": ["positive", "neutral", "negative"],
              "description": "Sentiment polarity toward this aspect."
            },
            "reason": {
              "type": "string",
              "description": "Short explanation or extracted text supporting the sentiment."
            }
          },
          "required": ["aspect_name", "sentiment", "reason"]
        }
      },
      "summary": {
        "type": "object",
        "properties": {
          "overall_sentiment": {
            "type": "string",
            "enum": ["positive", "neutral", "negative"],
            "description": "Overall sentiment across all aspects."
          },
          "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Summarised strengths mentioned in the review."
          },
          "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Summarised weaknesses mentioned in the review."
          }
        },
        "required": ["overall_sentiment"]
      }
    },
    "required": ["product_id", "product_name", "review_text", "aspects"],
    "additionalProperties": False
  },
  "strict": True
}
