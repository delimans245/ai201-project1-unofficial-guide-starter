from __future__ import annotations

import gradio as gr

from query import ask

EXAMPLES = [
    "What does BSC say a room-and-board house costs per semester, and what is included?",
    "Which BSC house is substance-free and academically themed?",
    "How does Apartment List describe Downtown Berkeley, and what drawback does it mention?",
    "What is the average rent for a 1-bedroom apartment in Berkeley according to Apartment List?",
    "What are the best pizza places near campus?",
]


def handle_query(question: str):
    result = ask(question)
    sources = "\n".join(f"• {source}" for source in result["sources"])
    if not sources:
        sources = "No supporting source was returned for this answer."
    return result["answer"], sources


with gr.Blocks(title="Berkeley Housing Unofficial Guide") as demo:
    gr.Markdown(
        "# Berkeley Housing Unofficial Guide\n"
        "Ask about off-campus housing, co-op costs, neighborhood tradeoffs, and scam warnings. "
        "The system answers only from the retrieved documents."
    )
    with gr.Row():
        question = gr.Textbox(label="Your question", placeholder="Ask about Berkeley housing...", lines=2)
    with gr.Row():
        submit = gr.Button("Ask")
    with gr.Row():
        answer = gr.Textbox(label="Answer", lines=8)
    with gr.Row():
        sources = gr.Textbox(label="Retrieved from", lines=6)

    gr.Examples(EXAMPLES, inputs=question)

    submit.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
