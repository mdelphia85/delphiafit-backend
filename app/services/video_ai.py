from datetime import datetime


class VideoAIService:

    def process_request(self, data):
        mode = data["mode"]

        # Placeholder — your GPU pipeline will replace this
        if mode == "breakdown":
            result = "Generated drill breakdown."
        elif mode == "highlight":
            result = "Generated highlight reel."
        elif mode == "commentary":
            result = "Generated AI commentary."
        else:
            result = "Unknown mode."

        return {
            "status": "processing",
            "mode": mode,
            "result": result,
            "requested_at": datetime.utcnow()
        }
