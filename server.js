// server.js (Backend en Node.js para gestionar Gemini y OpenAI con Failover)
const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());
app.use(express.static('public')); // Carpeta donde guardas tu HTML

// Tus claves de API protegidas en variables de entorno del servidor
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

app.post('/api/chat', async (req, res) => {
    const { messages, lang } = req.body;

    const systemPrompt = lang === 'es' 
        ? "Eres un asesor experto de bienestar y estilo de vida. Mantén el hilo de la conversación, sé conciso, directo, empático y guía al usuario paso a paso sin perder la coherencia de las preguntas anteriores."
        : "You are an expert wellness and lifestyle advisor. Maintain the conversation thread, be concise, direct, empathetic, and guide the user step-by-step without losing coherence from previous questions.";

    // 1. INTENTO PRINCIPAL: GEMINI API
    try {
        // Formatear historial para Gemini
        const formattedGeminiContents = messages.map(m => ({
            role: m.role === 'user' ? 'user' : 'model',
            parts: [{ text: m.content }]
        }));

        const geminiResponse = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
            {
                system_instruction: { parts: [{ text: systemPrompt }] },
                contents: formattedGeminiContents
            }
        );

        const reply = geminiResponse.data.candidates[0].content.parts[0].text;
        return res.json({ reply, provider: 'gemini' });

    } catch (geminiError) {
        console.warn('Gemini falló o no respondió. Activando respaldo con OpenAI...', geminiError.message);

        // 2. RESPALDO AUTOMÁTICO: OPENAI API
        try {
            const formattedOpenAIMessages = [
                { role: 'system', content: systemPrompt },
                ...messages
            ];

            const openAIResponse = await axios.post(
                'https://api.openai.com/v1/chat/completions',
                {
                    model: 'gpt-4o-mini',
                    messages: formattedOpenAIMessages,
                    temperature: 0.7
                },
                {
                    headers: {
                        'Authorization': `Bearer ${OPENAI_API_KEY}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const reply = openAIResponse.data.choices[0].message.content;
            return res.json({ reply, provider: 'openai' });

        } catch (openaiError) {
            console.error('Ambas APIs fallaron:', openaiError.message);
            return res.status(500).json({ error: 'No se pudo procesar la respuesta con las IA.' });
        }
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Servidor activo en el puerto ${PORT}`));
