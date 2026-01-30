from services.create_rag_chain import create_rag_chain


def tool_function(user_input: str, phase_id: str):
    
    qa_system_prompt = (
            "Sử dụng các thông tin bên dưới để trả lời câu hỏi của người dùng."
            "Nếu có phần nội dung không liên quan đến câu hỏi của người dùng, đánh dấu là [Không liên quan]"
            "và hiển thị như vậy khi phản hồi lại cho người dùng"
            "\n\n"
            "{context}"
        )

    rag_chain = create_rag_chain(phase_id, qa_system_prompt, user_input)

    return rag_chain.invoke(
        {"input": user_input}
    )
