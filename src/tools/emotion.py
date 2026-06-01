class EmotionDetector:
    EMOTIONS = {
        "happy": {"keywords": ["amazing","awesome","great","fantastic","love","excited","happy","wonderful","yay","perfect","excellent","thrilled","glad"],"tone": "Match their energy! Be enthusiastic and celebratory.","emoji": "😊","response_style": "upbeat"},
        "sad": {"keywords": ["sad","depressed","unhappy","miserable","crying","upset","heartbroken","lonely","hopeless","terrible","awful","hate my life","feel bad"],"tone": "Be warm, empathetic and supportive. Acknowledge their feelings first.","emoji": "💙","response_style": "gentle"},
        "frustrated": {"keywords": ["frustrated","annoyed","angry","mad","hate","stupid","not working","broken","useless","so annoying","ugh","argh","wtf"],"tone": "Stay calm and solution-focused. Acknowledge the frustration briefly then help.","emoji": "🤝","response_style": "calm_helpful"},
        "anxious": {"keywords": ["worried","anxious","scared","nervous","stress","stressed","overwhelmed","panic","afraid","fear","too much","pressure","failing"],"tone": "Be reassuring and structured. Break things into small clear steps.","emoji": "🌟","response_style": "reassuring"},
        "curious": {"keywords": ["how does","why does","curious","interesting","fascinating","i wonder","tell me more","teach me"],"tone": "Be engaging and thorough. Feed their curiosity.","emoji": "🧠","response_style": "engaging"},
        "confident": {"keywords": ["i can","i will","lets go","ready","lets build","im going to","bring it","definitely","absolutely"],"tone": "Match their confidence. Be direct and action-oriented.","emoji": "💪","response_style": "direct"},
        "bored": {"keywords": ["bored","boring","nothing to do","meh","whatever","so slow","not interesting","dull"],"tone": "Be lively and engaging. Suggest interesting ideas.","emoji": "✨","response_style": "lively"}
    }

    def detect(self, message):
        msg = message.lower()
        scores = {}
        for emotion, data in self.EMOTIONS.items():
            score = sum(1 for kw in data["keywords"] if kw in msg)
            if score > 0:
                scores[emotion] = score
        if not scores:
            return {"emotion": "neutral", "confidence": 1.0, "tone": "Be helpful, clear and friendly.", "emoji": "🤖", "response_style": "default"}
        top = max(scores, key=scores.get)
        return {"emotion": top, "confidence": min(scores[top]/3, 1.0), "tone": self.EMOTIONS[top]["tone"], "emoji": self.EMOTIONS[top]["emoji"], "response_style": self.EMOTIONS[top]["response_style"]}

    def get_system_addon(self, emotion_data):
        if emotion_data["emotion"] == "neutral":
            return ""
        return f"\n\n[EMOTIONAL CONTEXT]\nUser feels: {emotion_data['emotion']}\nTone: {emotion_data['tone']}"

    def format_emotion_display(self, emotion_data):
        return {"emotion": emotion_data["emotion"], "emoji": emotion_data["emoji"], "confidence": emotion_data["confidence"]}