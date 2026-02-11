from fastapi import APIRouter, HTTPException, Request
from fastapi import Body
from fastapi.responses import JSONResponse
from database.db import signup_collection, postlist_collection
from models.post import (UploadPost,ContentPage,ConclusionSlide)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from html2image import Html2Image
from dotenv import load_dotenv
import os, uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()



router = APIRouter()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2")



templates = Jinja2Templates(directory="templates")


llm_primary = None
llm_backup = None

if GOOGLE_API_KEY:
    try:
        llm_primary = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=GOOGLE_API_KEY
        )
        print("✅ Primary Gemini key loaded")
    except Exception as e:
        print(f"❌ Primary Gemini init failed: {e}")

if GOOGLE_API_KEY_2:
    try:
        llm_backup = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=GOOGLE_API_KEY_2
        )
        print("✅ Backup Gemini key loaded")
    except Exception as e:
        print(f"❌ Backup Gemini init failed: {e}")

if not llm_primary and not llm_backup:
    print("⚠️ No Gemini API keys available")



cloudinary.config(
    cloud_name="diba1hubd",
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

prompt1 = PromptTemplate(
        template="""
    You are generating structured text content for an Instagram carousel post.

    Use the following input data:
    - Post Title: {title}

    Your task:
    Design the output text to match the style of the reference Instagram post image.

    1. Add a short supporting Short and impactful description that reference to the title 
    (similar to: “heres why protein isn’t just for muscles – it’s essential to rebuild your skin color back!.Do NOT repeat, restate, or include the post title (or any variation of it) in the output text.
    The response must start directly with the supporting explanation content.

    Tone & Style Guidelines:
    - Clean, bold, and educational
    - Short and impactful sentences
    - Instagram-friendly wording
    - The bracketed description should explain *why* the topic matters

    Output Rules:
    - Return ONLY the formatted text content
    - Do NOT add explanations
    - Do include emojis

    """,
        input_variables=["title"],
)



prompt2 = PromptTemplate(
    template="""
    You are an expert Instagram carousel content writer. 
    
    REFERENCE CONTEXT (Not for direct use on content slides):
    Main Topic/Intro Title: {title}
    Detailed Description: {description}

    TASK:
    Generate content for the INNER SLIDES of the carousel. 
    Do NOT use the Main Title "{title}" as a heading on these slides. 
    Instead, create a unique, specific sub-heading for each slide that relates to the reference context.

    STYLE:
    - Educational, high-authority tone.
    - Simple wording, short sentences.
    - No markdown, no HTML, no hashtags.

    RULES:
    - Total content slides = {noOfPages} minus 2.
    - Each slide MUST have:
        1. A UNIQUE SUB-HEADING (Max 8 words) - This is the "Title Placeholder" in the HTML.
        2. EXACTLY FOUR CHUNKS of text (Each chunk max 20 words).
    - Each slide Short and impactful sentences
    - Chunk 1: Define the specific sub-topic of the slide.
    - Chunk 2 & 3: Detailed explanation or "Did you know?" facts.
    - Chunk 4: A "micro-call-to-action" or a transition to the next thought.

    OUTPUT FORMAT (STRICT):

    Slide 1:
    HEADING: [Unique Sub-heading 1]
    CHUNK 1: [Text]
    CHUNK 2: [Text]
    CHUNK 3: [Text]
    CHUNK 4: [Text]

    Slide 2:
    HEADING: [Unique Sub-heading 2]
    CHUNK 1: [Text]
    CHUNK 2: [Text]
    CHUNK 3: [Text]
    CHUNK 4: [Text]

    Continue until {noOfPages} minus 2 is reached.
    """,
        input_variables=["title", "description", "noOfPages"],

)


prompt3 = PromptTemplate(
    template="""
    You are an expert Instagram carousel content writer.

    Generate TEXT ONLY.
    emojis.
    No markdown.
    No HTML.
    No explanations.

    This is the FINAL SLIDE of an Instagram carousel.
    The text must look exactly like what appears on the last post slide.

    Style:
    - Black background
    - Clean
    - Clear conclusion
    - Educational + call-to-action
    - Short paragraphs

    Rules:
    - Start with a clear CONCLUSION HEADING
    - Summarize the main takeaway of the post
    - Give a practical recommendation or insight
    - End with a strong call-to-action (follow, comment, DM, etc.)
    - Show the account username clearly
    - No hashtags
    - No captions
    - No extra formatting

    INPUT:
    Title: {title}
    Account Name: {accName}
    Account Username: {accUsername}

    OUTPUT FORMAT (STRICT):

    SLIDE_TYPE: CONCLUSION
    HEADING: <short conclusion heading>
    SUMMARY_LINE_1: <supporting insight or advice>
    SUMMARY_LINE_2: <final tip, action step, or encouragement>
    CTA_LINE_1: <what action to take: follow / comment / DM>
    CTA_LINE_2: <account username>

    Only output content that would be visible on the final slide.
    """,
        input_variables=["title", "accName", "accUsername"],
)



html_intro ="""
       <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">

    <style>
    /* HARD RESET — THIS IS CRITICAL */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        width: 1080px;
        height: 1350px;
        background: #000;
    }
    </style>
    </head>

    <body>
    <div style="width: 1080px; height: 1350px; background-color: #000000; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; padding: 0; box-sizing: border-box; position: relative; overflow: hidden;">
        
        <div style="height: 60px;"></div>



        <div style="margin: 40px 60px 0 60px; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="width: 110px; height: 110px; border-radius: 50%; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); padding: 4px; display: flex; justify-content: center; align-items: center;">
                    <div style="width: 100%; height: 100%; border-radius: 50%; background-color: #333; overflow: hidden; border: 4px solid #000;">
                        <img src="https://picsum.photos/id/1/200/300" alt="Profile" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                </div>
                <div>
                    <div style="font-size: 34px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                       [FullName] 
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="#3897f0"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm5.1 8.9l-5.1 5.1c-.2.2-.4.3-.7.3s-.5-.1-.7-.3l-2.6-2.6c-.4-.4-.4-1 0-1.4s1-.4 1.4 0l1.9 1.9 4.4-4.4c.4-.4 1-.4 1.4 0s.4 1 0 1.4z"/></svg>
                    </div>
                    <div style="font-size: 28px; color: #8e8e8e;">[username]</div>
                </div>
            </div>
        </div>

        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 80px; text-align: center;">
            <h1 style="font-size: 65px; line-height: 1.5; font-weight: 800; margin-bottom: 40px;">
               [title]
            </h1>
            
            <div style="height: 250px; width: 100%;"></div>

            <p style="font-size: 35px; line-height: 1.5; color: #ffffff; font-style: italic; max-width: 800px;">
            (Tdesc)
            </p>
        </div>
    </div>

"""


html_content =""" 
                <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">

    <style>
    /* HARD RESET — THIS IS CRITICAL */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        width: 1080px;
        height: 1350px;
        background: #000;
    }
    </style>
    </head>

    <body>
    <div style="width: 1080px; height: 1350px; background-color: #000000; color: #ffffff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; display: flex; flex-direction: column; box-sizing: border-box; position: relative; overflow: hidden; padding: 100px 80px;">

    <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-start; text-align: left;">
        
        <h1 style="font-size: 60px; line-height: 1.5; font-weight: 700; margin-bottom: 70px; letter-spacing: -1px; color: #ffffff;">
          [Title Placeholder]
        </h1>

        <div style="display: flex; flex-direction: column; gap: 50px;">
            
            <p style="font-size: 45px; line-height: 1.5; color: #ffffff; margin: 10; font-weight: 400;">
                [First chunk]
            </p>

            <p style="font-size: 45px; line-height: 1.5; color: #ffffff; margin: 10; font-weight: 400;">
                [Second chunk]
            </p>

            <p style="font-size: 45px; line-height: 1.5; color: #ffffff; margin: 10; font-weight: 400;">
                [Third chunk]
            </p>

            <p style="font-size: 45px; line-height: 1.5; color: #ffffff; margin: 10; font-weight: 400;">
                [Final chunk]
            </p>

        </div>
    </div>

    <div style="width: 100%; display: flex; justify-content: center; align-items: center; position: relative; padding-bottom: 40px;">
   
    
    </div>

  </div>

    </body>
    </html>


"""


html_conclusion = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">

    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        background: #000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    .slide {
		min-height: 100vh;
        width: 100%;
        background: #000;
        color: #fff;
        padding: 80px;
        display: flex;
        flex-direction: column;
    }

    /* Title */
    .slide-title {
        font-size: 60px;
        font-weight: 700;
        line-height: 1.50;
        margin-bottom: 70px;
    }

    /* Content */
    .slide-content {
        font-size: 50px;
        line-height: 1.5;
    }

    .slide-content p {
        margin-bottom: 80px;
    }

    /* Follow section */
    .follow-section {
        position: relative;
        bottom: 150px;
        left: 0;
        width: 100%;
        text-align: center;
    }

    .follow-text {
        font-size: 60px;
        margin-top: 50px;
        position: absolute;
        top: 200px
    }

    .username {
        font-weight: 600;
    }
    </style>
    </head>

    <body>

    <div class="slide">

        <h1 class="slide-title">
         [Conclusion]
        </h1>

        <div class="slide-content">
            <p>[line1].</p>
            <p>[line2].</p>
        </div>

        <div class="follow-section">
            <p class="follow-text">
                [action]  <span class="username">@[username]</span>
            </p>
        </div>

    </div>

    </body>
    </html>
"""




def safe_llm_invoke(prompt_chain, input_data):
    try:
        if llm_primary:
            return (prompt_chain | llm_primary | StrOutputParser()).invoke(input_data)

        raise Exception("Primary LLM not available")

    except Exception as e:
        error_msg = str(e).lower()

        if any(k in error_msg for k in ["quota", "rate", "limit", "exceeded"]):
            if llm_backup:
                print("⚠️ Primary key exhausted, switching to backup key")
                return (prompt_chain | llm_backup | StrOutputParser()).invoke(input_data)

        raise e


@router.post("/respone",response_class=HTMLResponse)
async def post_create(data:UploadPost) :

    #1st page genrate
    out1 = safe_llm_invoke(prompt1, {
        "title": data.title
    })

    intro_html = (
    html_intro
    .replace("[FullName]" , data.accName, 1)
    .replace("[username]", data.accUsername,1)
    .replace("org_url", data.imageUrl,1)
    .replace("[title]", data.title,1)
    .replace(" (Tdesc)", out1,1)
    )


    #2nd pages genrates
    total_pages = data.noOfPages
    content_slide_count = max(total_pages - 2, 0)

    out2 = safe_llm_invoke(prompt2, {
    "title": data.title,
    "description": data.description,
    "noOfPages": data.noOfPages
    })


    raw_slides = out2.split("\n\n")
    content_pages = []

        # ✅ LOOP MUST CONTAIN PARSING LOGIC
    for i, page in enumerate(raw_slides):
        if i >= content_slide_count:
            break

        lines = page.strip().split("\n")
        heading = ""
        chunks = {"chunk1": "", "chunk2": "", "chunk3": "", "chunk4": ""}

        for line in lines:
            if line.startswith("HEADING:"):
                heading = line.replace("HEADING:", "").strip()
            elif line.startswith("CHUNK 1:"):
                chunks["chunk1"] = line.replace("CHUNK 1:", "").strip()
            elif line.startswith("CHUNK 2:"):
                chunks["chunk2"] = line.replace("CHUNK 2:", "").strip()
            elif line.startswith("CHUNK 3:"):
                chunks["chunk3"] = line.replace("CHUNK 3:", "").strip()
            elif line.startswith("CHUNK 4:"):
                chunks["chunk4"] = line.replace("CHUNK 4:", "").strip()

        content_pages.append(
            ContentPage(
                page_no=i + 1,
                heading=heading,
                **chunks
            )
        )

    html_slides = []

    for page in content_pages:
        slide_html = (
            html_content
            .replace("[Title Placeholder]", page.heading, 1)
            .replace("[First chunk]", page.chunk1, 1)
            .replace("[Second chunk]", page.chunk2, 1)
            .replace("[Third chunk]", page.chunk3, 1)
            .replace("[Final chunk]", page.chunk4, 1)
        )

        # ✅ YOU MISSED THIS
        html_slides.append(slide_html)

    content_html = "\n".join(html_slides)



    #final page genrate
    out3 = safe_llm_invoke(prompt3, {
    "title": data.title,
    "accName": data.accName,
    "accUsername": data.accUsername
    })


    final_page = []


    clines = out3.split("\n")

    Conclusion = ""
    line1 = ""
    line2 = ""
    action = ""

    for line in clines:
        if line.startswith("HEADING:"):
            Conclusion = line.replace("HEADING:", "").strip()
        if line.startswith("SUMMARY_LINE_1:"):
            line1 = line.replace("SUMMARY_LINE_1:", "").strip()
        if line.startswith("SUMMARY_LINE_2:"):
            line2 = line.replace("SUMMARY_LINE_2:", "").strip()
        if line.startswith("CTA_LINE_1:"):
            action = line.replace("CTA_LINE_1:", "").strip()

    final_page.append(
        ConclusionSlide(
        type = "conclusion",
        title = Conclusion,
        line1 = line1,
        line2 = line2,
        action = action
        )
    )

    final_html = (
            html_conclusion
            .replace("[Conclusion]", final_page[0].title, 1)
            .replace("[line1]", final_page[0].line1, 1)
            .replace("[line2]", final_page[0].line2, 1)
            .replace("[action]", final_page[0].action, 1)
            .replace("[username]", data.accUsername, 1)

        )

    slides_html = [intro_html, content_html, final_html]
    combined_html = "\n".join(slides_html)


     
    return HTMLResponse(content=combined_html)
    

OUTPUT_DIR = os.path.join(os.getcwd(), "gen_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)



@router.post("/htmlconverter")
def htmltoimage(html_content: str = Body(..., media_type="text/plain")):

    parts = html_content.split('<!DOCTYPE html>')

    expanded_list = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        expanded_list.append('<!DOCTYPE html>' + part)

    if not expanded_list:
        raise HTTPException(status_code=400, detail="No HTML found")

    image_urls = []

    for index, html in enumerate(expanded_list, start=1):

        # Temporary local file
        temp_filename = f"{uuid.uuid4()}_{index}.png"

        hti = Html2Image()
        hti.screenshot(
            html_str=html,
            save_as=temp_filename,
            size=(1080, 1350)
        )

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            temp_filename,
            folder="instagram_carousels",
            public_id=f"slide_{uuid.uuid4()}",
            overwrite=True,
            resource_type="image"
        )

        # Save Cloudinary URL
        image_urls.append(upload_result["secure_url"])

        # Delete local temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return JSONResponse({
        "message": "HTML converted to images and uploaded to Cloudinary",
        "images": image_urls
    })
