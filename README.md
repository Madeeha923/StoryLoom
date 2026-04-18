# StoryLoom 

**From Local Heritage to Global Markets: Empowering Artisans with One-Click AI Studio.**

StoryLoom is an all-in-one AI platform designed specifically to bridge the digital gap for local craftworkers and artisans. The mission is simple: to promote traditional craftsmanship at a world-class level by removing all technical and marketing barriers.

---

## 📽️ Project Demo
See how StoryLoom transforms a simple craft into a global brand:  
**[Watch the Demo Video Here](YOUR_VIDEO_DEMO_LINK_HERE)**

---

##  Why StoryLoom?

### 1. Built for Everyone (Zero Technical Barrier)
StoryLoom is designed for users who may have little to no knowledge of technology. There is no need for complex "prompt engineering" or professional photography skills.
* **Speak or Type**: Artisans can provide a very short description of their product. If they are unable to write, they can simply **speak** into the app. The system automatically transcribes and understands their voice note.
* **All-in-One Platform**: No need to use different apps for editing, writing, or listing. StoryLoom handles everything in one workspace.

### 2. Professional Assets, Automatically
The platform uses a sophisticated multi-agent system to turn basic input into premium marketing content:
* **Automatic Descriptions**: Generates high-end, professional product narratives designed to attract international buyers.
* **Studio Visuals**: Automatically synthesizes high-quality, professional-grade lifestyle images of the product.
* **Campaign Video**: Creates a timed slideshow preview of the product for social media engagement.

### 3. Global Selling with Automatic Upload
The main motive is to help artisans sell their products globally and promote their work.
* **Marketplace Integration**: The app automatically prepares a structured "Upload Package" for the **ONDC (Open Network for Digital Commerce)** ecosystem.
* **User Account Connection**: The system is designed to automatically upload these listings to e-commerce websites using the user's own account (this feature currently uses a mock endpoint and requires future API authentication integration).

---

## The Multi-Agentic Engine
StoryLoom was built using a **Sequential Multi-Agent Orchestration** engine. Seven specialized AI agents work together as a professional marketing and technical team:

1.  **Input Agent**: Processes the artisan’s text or voice notes to define the product brief.
2.  **Visionary Agent**: Analyzes the raw photo to identify colors, textures, and craft details.
3.  **Historian Agent**: Adds cultural and historical depth to the product story.
4.  **Copywriter Agent**: Crafts the final professional description.
5.  **Studio Agent**: Plans the visual campaign and video script.
6.  **Image Generator Agent**: Creates the professional campaign images.
7.  **Registrar Agent**: Packages everything for automatic e-commerce listing.

---

##  Technical Stack
* **Backend**: FastAPI (Python) for modular orchestration.
* **Frontend**: React (Vite) with a minimalist, accessible UI.
* **AI Engine**: GPT-4o for vision and text analysis, and DALL-E 3 for image generation.
* **Protocol**: ONDC / Beckn Protocol mock integration for digital commerce.

---

<!-- ## Getting Started

### 1. Backend Setup
```bash
# Navigate to the app directory
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API Key to .env and set image models to dall-e-3
uvicorn app.main:app --reload -->