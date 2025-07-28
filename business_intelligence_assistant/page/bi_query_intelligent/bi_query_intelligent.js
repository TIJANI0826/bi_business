frappe.pages['bi-query-intelligent'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'BI Assistant',
        single_column: true
    });
    
    // Navbar Integration
    page.set_secondary_action('Sync Table Metadata', () => {
        frappe.call({
            method: 'bi_assisstant.business_intelligence_assistant.bi_assistant.sync_table_metadata',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Table metadata synced successfully'));
                }
            }
        });
    }, 'fa fa-refresh');

    // Load marked.js for Markdown rendering
    frappe.require('https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js');

    // Main Chat UI Container
    let chat_container = $(
        `<div style="padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;">
            <div class="chat-messages" style="max-height: 400px; overflow-y: auto;"></div>
        </div>`
    ).appendTo(page.main);

    // Chat Input Box (Fixed at Bottom)
    let chat_input_container = $(
        `<div style="display: flex; gap: 10px; margin-top: 10px;">
            <textarea class="form-control chat-input" placeholder="Ask a business question..." style="flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #ccc;"></textarea>
            <button class="btn btn-primary chat-send" style="padding: 10px 20px; border-radius: 5px;">Send</button>
        </div>`
    ).appendTo(page.main);

    let chat_messages = chat_container.find('.chat-messages');
    let chat_input = chat_input_container.find('.chat-input');
    let chat_send_button = chat_input_container.find('.chat-send');

    // Function to safely render Markdown
    function renderMarkdown(text) {
        return marked.parse(text);
    }

    // Function to get current time as HH:MM:SS
    function getCurrentTime() {
        return new Date().toLocaleTimeString();
    }

    // Function to handle streaming response using frappe.call
    function streamResponse(question, timestamp) {
        let assistantMessage = $(
            `<div class="chat-message assistant-message" style="margin: 10px 0; padding: 10px; background-color: #e9ecef; border-radius: 5px;">
                <b>BI Assistant:</b> <span class="response-content"></span>
                <div style="font-size: 12px; color: gray; margin-top: 5px;">Response received at: <span class="response-time"></span></div>
            </div>`
        );
        chat_messages.append(assistantMessage);
        let responseContent = assistantMessage.find('.response-content');
        let responseTime = assistantMessage.find('.response-time');

        frappe.call({
            method: 'bi_assisstant.business_intelligence_assistant.testAgno.run_agent',
            args: { question: question },
            freeze: true,
            freeze_message: "BI Assistant is thinking...",
            callback: function(r) {
                if (r.message) {
                    responseContent.html(renderMarkdown(r.message));
                    responseTime.text(getCurrentTime());
                    chat_messages.scrollTop(chat_messages.prop("scrollHeight")); // Auto-scroll
                }
            }
        });
    }

    // Handle Query Submission
    chat_send_button.click(() => {
        let question = chat_input.val().trim();
        if (!question) {
            frappe.msgprint(__('Please enter a question'));
            return;
        }

        let timestamp = getCurrentTime();

        // Display user message
        chat_messages.append(
            `<div class="chat-message user-message" style="margin: 10px 0; padding: 10px; background-color: #d1ecf1; border-radius: 5px;">
                <b>You:</b> ${question}
                <div style="font-size: 12px; color: gray; margin-top: 5px;">Sent at: ${timestamp}</div>
            </div>`
        );
        chat_input.val(''); // Clear input field
        
        streamResponse(question, timestamp);
    });     
    
    let container = $('<div class="bi-ui-container" style="margin-top: 20px;"></div>').appendTo(page.main);
    
    // Saved Queries Section
    let saved_queries_container = $('<div class="saved-queries-container" style="margin-top: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #ffffff;"><h4>Saved Queries</h4></div>').appendTo(container);
    frappe.call({
        method: 'bi_assisstant.business_intelligence_assistant.bi_assistant.get_sample_queries',
        callback: function(r) {
            if (r.message) {
                r.message.forEach(q => {
                    let btn = $(
                        `<button class="btn btn-light" style="display: block; width: 100%; margin-bottom: 5px; padding: 10px; text-align: left; border-radius: 5px;">${q.title}</button>`
                    ).appendTo(saved_queries_container);
                    btn.click(() => chat_input.val(q.query));
                });
            }
        }
    });
    
    $('<div class="space_saved_query" style="margin-top: 10px;"><hr></div>').appendTo(container);
};
