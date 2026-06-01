"""
Lynthz Emotion Detection Tool
Detects user emotions and adjusts response tone accordingly.
No API key needed — rule-based + keyword detection.
"""

from typing import Optional


class EmotionDetector:
    
    EMOTIONS = {
        "happy": {
            "keywords": ["amazing", "awesome", "great", "fantastic", "love", "excited",
                        "happy", "wonderful", "brilliant", "yay", "woohoo", "perfect",
                        "excellent", "thrilled", "glad", "joy", "best day", "so good"],
            "tone": "Match their energy! Be enthusiastic and celebratory.",
            "emoji": "😊",
            "response_style": "upbeat"
        },
        "sad": {
            "keywords": ["sad", "depressed", "unhappy", "miserable", "crying", "upset",
                        "heartbroken", "lonely", "lost", "hopeless", "terrible", "awful",
                        "worst day", "hate my life", "feel bad", "i miss", "grief"],
            "tone": "Be warm, empathetic and supportive. Acknowledge their feelings first.",
            "emoji": "💙",
            "response_style": "gentle"
        },
        "frustrated": {
            "keywords": ["frustrated", "annoyed", "angry", "mad", "hate", "stupid",
                        "not working", "broken", "useless", "terrible", "why wont",
                        "keeps failing", "so annoying", "ugh", "argh", "damn", "wtf"],
            "tone": "Stay calm and solution-focused. Acknowledge the frustration briefly then help.",
            "emoji": "🤝",
            "response_style": "calm_helpful"
        },
        "anxious": {
            "keywords": ["worried", "anxious", "scared", "nervous", "stress", "stressed",
                        "overwhelmed", "panic", "afraid", "fear", "cant sleep", "too much",
                        "pressure", "deadline", "failing", "what if", "confused"],
            "tone": "Be reassuring and structured. Break things into small clear steps.",
            "emoji": "🌟",
            "response_style": "reassuring"
        },
        "curious": {
            "keywords": ["how does", "why does", "what if", "curious", "interesting",
                        "fascinating", "i wonder", "can you explain", "tell me more",
                        "how come", "what happens", "i want to learn", "teach me"],
            "tone": "Be engaging and thorough. Feed their curiosity with interesting details.",
            "emoji": "🧠",
            "response_style": "engaging"
        },
        "confident": {
            "keywords": ["i can", "i will", "lets do", "lets go", "ready", "lets build",
                        "i want to create", "im going to", "challenge accepted", "bring it",
                        "i know", "definitely", "absolutely", "for sure"],
            "tone": "Match their confidence. Be direct, energetic and action-oriented.",
            "emoji": "💪",
            "response_style": "direct"
        },
        "bored": {
            "keywords": ["bored", "boring", "nothing to do", "meh", "whatever", "so slow",
                        "not interesting", "dull", "monotonous", "same old", "tired of"],
            "tone": "Be lively and engaging. Suggest interesting ideas or perspectives.",
            "emoji": "✨",
            "response_style": "lively"
        }
    }

    INTENSITY_AMPLIFIERS = ["very", "so", "really", "extremely", "super", "too", "absolutely"]

    def detect(self, message: str) -> dict:
        """Detect emotion from message."""
        msg = message.lower()
        
        scores = {}
        for emotion, data in self.EMOTIONS.items():
            score = sum(1 for kw in data["keywords"] if kw in msg)
            # Boost score if intensity amplifiers present
            if score > 0:
                boost = sum(1 for amp in self.INTENSITY_AMPLIFIERS if amp in msg)
                score += boost * 0.5
            if score > 0:
                scores[emotion] = score

        if not scores:
            return {
                "emotion": "neutral",
                "confidence": 1.0,
                "tone": "Be helpful, clear and friendly.",
                "emoji": "🤖",
                "response_style": "default"
            }

        top_emotion = max(scores, key=scores.get)
        top_score = scores[top_emotion]
        confidence = min(top_score / 3, 1.0)

        return {
            "emotion": top_emotion,
            "confidence": round(confidence, 2),
            "tone": self.EMOTIONS[top_emotion]["tone"],
            "emoji": self.EMOTIONS[top_emotion]["emoji"],
            "response_style": self.EMOTIONS[top_emotion]["response_style"],
            "all_scores": scores
        }

    def get_system_addon(self, emotion_data: dict) -> str:
        """Generate system prompt addition based on emotion."""
        emotion = emotion_data["emotion"]
        tone = emotion_data["tone"]
        style = emotion_data["response_style"]

        if emotion == "neutral":
            return ""

        addon = f"\n\n[EMOTIONAL CONTEXT]\n"
        addon += f"User appears to be feeling: {emotion}\n"
        addon += f"Tone guidance: {tone}\n"

        style_guides = {
            "upbeat": "Use positive language, maybe add some enthusiasm. Keep energy high.",
            "gentle": "Start with empathy. Use soft language. Avoid being too direct or harsh.",
            "calm_helpful": "Acknowledge frustration in one sentence, then focus on solutions.",
            "reassuring": "Use calming language. Break response into clear steps. Be patient.",
            "engaging": "Be enthusiastic about the topic. Add interesting details and examples.",
            "direct": "Be confident and action-oriented. No hedging. Give clear next steps.",
            "lively": "Be energetic and interesting. Suggest new ideas or fun perspectives."
        }

        addon += f"Style: {style_guides.get(style, '')}"
        return addon

    def format_emotion_display(self, emotion_data: dict) -> dict:
        """Format for frontend display."""
        return {
            "emotion": emotion_data["emotion"],
            "emoji": emotion_data["emoji"],
            "confidence": emotion_data["confidence"]
        }
