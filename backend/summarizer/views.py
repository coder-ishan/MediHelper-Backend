# Set up logging
import logging
import os
import time
import fitz  # PyMuPDF
import json
import openai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings


logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@api_view(['GET'])
def get_text_from_pdf(request, pdf_file_path):
    return Response({"recieving...testing...."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def upload_and_summarize(request):
    # Check if the file is provided in the request
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    file_name = uploaded_file.name

    # Save the file temporarily
    temp_file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    with open(temp_file_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    # Extract text from the PDF using PyMuPDF
    try:
        doc = fitz.open(temp_file_path)
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text("text")  # Specify 'text' explicitly for cleaner output

        # Summarize using OpenAI API
        summary = generate_summary(text)
        #print(summary)

        return Response(summary, status=status.HTTP_200_OK)
    except Exception as e: 
        # Log the error and clean up the file
        time.sleep(5)
        os.remove(temp_file_path)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def answer_question(question):
    with open('db.json', 'r') as f:
        context = json.load(f)["summary"]
    response = openai.Completion.create(
        model="gpt-4",
        question=question,
        documents=[context]
    )
    return response.answers[0].answer


def generate_summary(text):
    input_chunks = split_text(text)
    output_chunks = []

    # promt template
    for chunk in input_chunks:
        chat_completion = openai.Completion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"As an expert in diagnostic medicine, analyze the provided lab report line by line. Identify and interpret all deviations from normal reference ranges, focusing on significant findings. Correlate these findings with potential clinical conditions and only provide a list of probable diagnoses. Additionally, offer recommendations for further evaluation or treatment based on the findings. Respond in a very concise, structured format with a focus on clinical relevance.The details are as follows: {chunk}"
                }
            ]
        )
        response = chat_completion.choices[0].message
        summary =response.content
        output_chunks.append(summary )
        final_summary = " "
        for chunk in output_chunks:
            final_summary += chunk
            final_summary += "\n"
        print(final_summary)
    final_summary_json = {
        "summary" : final_summary.strip()
    }
    with open('db.json', 'w') as f:
        json.dump(final_summary_json, f)

    return final_summary_json
    





# Semantic chunker
def split_text(text):
    max_chunk_size = 2048
    chunks = []
    current_chunk = ""
    for sentence in text.split("."):
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + "."
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks
