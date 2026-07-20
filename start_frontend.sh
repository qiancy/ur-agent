#!/bin/bash

# 启动前端服务
echo "启动前端服务..."

# 解析参数
DAEMON=false
if [ "$1" == "--daemon" ]; then
    DAEMON=true
fi

# 启动Gradio前端
CMD="python3 -c '
import gradio as gr
from src.agents.agent import create_uni_resource_agent

# 创建Agent
agent = create_uni_resource_agent()

def predict(input_text):
    try:
        result = agent.invoke({\"input\": input_text})
        return result[\"output\"]
    except Exception as e:
        return str(e)

# 创建Gradio界面
with gr.Blocks(title=\"Uni-Resource Agent\") as demo:
    gr.Markdown(\"# Uni-Resource Agent\")
    gr.Markdown(\"统一资源管理AI助手\")
    input_text = gr.Textbox(label=\"输入问题\", placeholder=\"请输入您的问题...\")
    output_text = gr.Textbox(label=\"回答\", interactive=False)
    button = gr.Button(\"提交\")
    
    button.click(
        fn=predict,
        inputs=input_text,
        outputs=output_text
    )
    
    input_text.submit(
        fn=predict,
        inputs=input_text,
        outputs=output_text
    )

demo.launch(server_name=\"0.0.0.0\", server_port=7860)
'"

if [ "$DAEMON" = true ]; then
    nohup $CMD > frontend.log 2>&1 &
else
    $CMD
fi
