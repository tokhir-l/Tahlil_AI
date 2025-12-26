import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { Message, FileAttachment } from '../types';

let client: GoogleGenAI | null = null;

const getClient = () => {
  if (!client) {
    // The API key must be obtained exclusively from the environment variable process.env.API_KEY.
    // Use this process.env.API_KEY string directly when initializing.
    client = new GoogleGenAI({ apiKey: process.env.API_KEY });
  }
  return client;
};

export const generateResponse = async (
  modelId: string,
  history: Message[],
  newMessage: string,
  attachments: FileAttachment[] = []
): Promise<{ text: string }> => {
  const ai = getClient();
  
  // Convert history to Gemini format (excluding system messages for now if needed, or mapping them)
  // Simple chat without history for MVP to avoid token limits, or last few messages
  // Using generateContent for single turn with context, or chats for session
  
  // Construct the prompt
  const parts: any[] = [];
  
  // Add attachments
  for (const file of attachments) {
    // Remove data:image/png;base64, prefix if present
    const base64Data = file.data.split(',')[1] || file.data;
    parts.push({
      inlineData: {
        mimeType: file.type,
        data: base64Data
      }
    });
  }

  // Add text prompt
  parts.push({ text: newMessage });

  // System instruction to act as Data Analyst
  const systemInstruction = "You are Tahlil, an advanced AI Data Science Analyst. You help users analyze data, understand complex files, and visualize trends. Be concise, professional, and helpful. If data is provided, try to present it in tables or clear lists.";

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: modelId,
      contents: {
        role: 'user',
        parts: parts
      },
      config: {
        systemInstruction: systemInstruction,
        // Optional: enable thinking if using 2.5-flash for deeper reasoning
        // thinkingConfig: { thinkingBudget: 1024 } // Only for supported models
      }
    });

    return { text: response.text || "I couldn't generate a response." };
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
};