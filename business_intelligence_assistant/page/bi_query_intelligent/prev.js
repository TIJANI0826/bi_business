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
    let chat_container = $(`
        <div class="bi-chat-container">
            <div class="chat-messages"></div>
        </div>
    `).appendTo(page.main);

    // Chat Input Box (Fixed at Bottom)
    let chat_input_container = $(`
        <div class="chat-input-container">
            <textarea class="form-control chat-input" placeholder="Ask a business question..."></textarea>
            <button class="btn btn-primary chat-send">Send</button>
        </div>
    `).appendTo(page.main);

    let chat_messages = chat_container.find('.chat-messages');
    let chat_input = chat_input_container.find('.chat-input');
    let chat_send_button = chat_input_container.find('.chat-send');

    // Function to safely render Markdown
    function renderMarkdown(text) {
        return marked.parse(text);
    }

    // Handle Query Submission
    chat_send_button.click(() => {
        let question = chat_input.val().trim();
        if (!question) {
            frappe.msgprint(__('Please enter a question'));
            return;
        }

        // Display user message
        chat_messages.append(`<div class="chat-message user-message"><b>You:</b> ${question}</div>`);
        chat_input.val(''); // Clear input field

        // Display assistant typing indicator
        let assistantMessage = $(`<div class="chat-message assistant-message"><b>BI Assistant:</b> <span class="loading">...</span></div>`);
        chat_messages.append(assistantMessage);
        chat_messages.scrollTop(chat_messages.prop("scrollHeight")); // Auto-scroll

        // Start Streaming Response
        frappe.call({
            method: 'bi_assisstant.business_intelligence_assistant.testAgno.run_agent',
            args: { question: question },
            freeze: true,
            freeze_message: "BI Assistant is thinking...",
            callback: function(r) {
                if (r.message) {
                    assistantMessage.find('.loading').remove();
                    let formattedResponse = renderMarkdown(r.message);
                    assistantMessage.append(formattedResponse);
                    chat_messages.scrollTop(chat_messages.prop("scrollHeight")); // Auto-scroll
                }
            }
        });
    });     
    
    let container = $('<div class="bi-ui-container"></div>').appendTo(page.main);
    
    // Saved Queries Section
    let saved_queries_container = $('<div class="saved-queries-container"><h4>Saved Queries</h4></div>').appendTo(container);
    frappe.call({
        method: 'bi_assisstant.business_intelligence_assistant.bi_assistant.get_sample_queries',
        callback: function(r) {
            if (r.message) {
                r.message.forEach(q => {
                    let btn = $(`<button class="btn btn-light">${q.title}</button>`).appendTo(saved_queries_container);
                    btn.click(() => chat_input.val(q.query));
                });
            }
        }
    });
    
    let space_saved_query = $('<div class="space_saved_query"><hr></div>').appendTo(container);

};
