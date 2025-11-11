"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ActivityLog {
  message: string;
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activityLog, setActivityLog] = useState<ActivityLog[]>([]);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [mealPlan, setMealPlan] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activityLogEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    activityLogEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activityLog]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 128)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send message on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        sendMessage(e as any);
      }
    }
  };

  const sendMessage = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }
    if (!input.trim() || isLoading) return;

    const messageToSend = input; // Keep original with line breaks
    
    const userMessage: Message = {
      role: "user",
      content: messageToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px';
    }
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5001/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: messageToSend,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      if (data.message) {
        const aiMessage: Message = {
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      }

      if (data.activity_log && Array.isArray(data.activity_log)) {
        setActivityLog(
          data.activity_log.map((msg: string) => ({
            message: msg,
            timestamp: new Date(),
          }))
        );
      }

      if (data.meal_plan) {
        setMealPlan(data.meal_plan);
      }

      // Poll for activity updates if meal plan is being generated
      if (data.ready_for_meal_plan) {
        pollActivityLog();
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please make sure the backend server is running on http://localhost:5001",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const pollActivityLog = async () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `http://localhost:5001/api/activity_log?session_id=${sessionId}`
        );
        const data = await response.json();

        if (data.activity_log && Array.isArray(data.activity_log)) {
          setActivityLog(
            data.activity_log.map((msg: string) => ({
              message: msg,
              timestamp: new Date(),
            }))
          );
        }

        if (data.status === "complete") {
          clearInterval(interval);
        }
      } catch (error) {
        console.error("Error polling activity log:", error);
        clearInterval(interval);
      }
    }, 1000);

    // Stop polling after 30 seconds
    setTimeout(() => clearInterval(interval), 30000);
  };

  const handleGetStarted = async () => {
    const message = "get started";
    const userMessage: Message = {
      role: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5001/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      if (data.message) {
        const aiMessage: Message = {
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      }

      if (data.activity_log && Array.isArray(data.activity_log)) {
        setActivityLog(
          data.activity_log.map((msg: string) => ({
            message: msg,
            timestamp: new Date(),
          }))
        );
      }

      if (data.meal_plan) {
        setMealPlan(data.meal_plan);
      }

      if (data.ready_for_meal_plan) {
        pollActivityLog();
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please make sure the backend server is running on http://localhost:5001",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Header */}
      <header className="bg-black border-b border-white p-4">
        <h1 className="text-2xl font-bold text-white">
          AI Nutrition Assistant
          </h1>
        <p className="text-sm text-gray-400">
          Affordable meal planning for your family
        </p>
      </header>

      <div className="flex-1 flex flex-col md:flex-row gap-4 p-4 overflow-hidden">
        {/* Chat Interface */}
        <div className="flex-1 flex flex-col bg-black border border-white rounded-lg overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold text-white mb-2">
                  Welcome to AI Nutrition Assistant!
                </h2>
                <p className="text-gray-400 mb-6">
                  Get personalized, affordable meal plans for your family
                </p>
                <button
                  onClick={handleGetStarted}
                  className="bg-white text-black font-bold py-3 px-8 rounded-lg border border-white hover:bg-gray-200 transition-colors"
                >
                  Get Started
                </button>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-white text-black border border-white"
                      : "bg-black text-white border border-white"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-black border border-white rounded-lg p-3">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-white rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-white rounded-full animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
        </div>

          {/* Input Form */}
          <form
            onSubmit={sendMessage}
            className="border-t border-white p-4 bg-black"
          >
            <div className="flex gap-2 items-end">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message... (Shift+Enter for new line)"
                rows={1}
                className="flex-1 px-4 py-2 bg-black border border-white text-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-white focus:border-white resize-none min-h-[44px] max-h-32 overflow-y-auto"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-white text-black font-bold py-2 px-6 rounded-lg border border-white hover:bg-gray-200 transition-colors disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed disabled:border-gray-800 h-[44px]"
              >
                Send
              </button>
            </div>
          </form>
        </div>

        {/* Activity Log & Meal Plan */}
        <div className="w-full md:w-96 flex flex-col gap-4">
          {/* Activity Log */}
          {activityLog.length > 0 && (
            <div className="bg-black border border-white rounded-lg p-4 overflow-hidden flex flex-col">
              <h3 className="font-bold text-white mb-2">Activity Log</h3>
              <div className="flex-1 overflow-y-auto space-y-2">
                {activityLog.map((log, index) => (
                  <div
                    key={index}
                    className="text-sm text-white bg-black border border-white p-2 rounded"
                  >
                    {log.message}
                  </div>
                ))}
                <div ref={activityLogEndRef} />
              </div>
            </div>
          )}

          {/* Meal Plan Display */}
          {mealPlan && (
            <div className="bg-black border border-white rounded-lg p-4 overflow-y-auto flex-1 space-y-4">
              {/* Weekly Summary */}
              {mealPlan.weekly_summary && (
                <div className="border border-white rounded-lg p-3 bg-black">
                  <h3 className="font-bold text-white mb-2">📊 Weekly Summary</h3>
                  <div className="space-y-1 text-sm text-white">
                    <p>Total Cost: ${mealPlan.weekly_summary.total_cost?.toFixed(2) || mealPlan.total_cost?.toFixed(2)}</p>
                    <p>Serves: {mealPlan.weekly_summary.serves} people</p>
                    <p>Location: {mealPlan.weekly_summary.location}</p>
                    <p>Budget Used: {mealPlan.weekly_summary.budget_utilization}</p>
                  </div>
                </div>
              )}

              {/* Grocery List */}
              {mealPlan.grocery_list && mealPlan.grocery_list.length > 0 && (
                <div className="border border-white rounded-lg p-3 bg-black">
                  <h3 className="font-bold text-white mb-2">🛒 Grocery List</h3>
                  <div className="space-y-1 text-xs max-h-40 overflow-y-auto">
                    {mealPlan.grocery_list.slice(0, 15).map((item: any, index: number) => (
                      <div key={index} className="text-gray-300 border-b border-gray-700 pb-1">
                        <p className="font-medium text-white">{item.ingredient}</p>
                        <p className="text-gray-400">
                          {item.quantity} {item.unit} - ${item.estimated_cost?.toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>
                  {mealPlan.total_grocery_cost && (
                    <p className="text-white font-semibold mt-2 text-sm">
                      Total: ${mealPlan.total_grocery_cost.toFixed(2)}
                    </p>
                  )}
                </div>
              )}

              {/* Meal Plan Days */}
              <div className="space-y-3">
                <h3 className="font-bold text-white">📅 Meal Plan</h3>
                {mealPlan.days?.map((day: any, index: number) => (
                  <div
                    key={index}
                    className="border border-white rounded-lg p-3 bg-black"
                  >
                    <h4 className="font-semibold text-white mb-2">{day.day}</h4>
                    <div className="space-y-2 text-sm">
                      {Object.entries(day.meals || {}).map(
                        ([mealType, meal]: [string, any]) => (
                          <div
                            key={mealType}
                            className="border-l-2 border-white pl-2"
                          >
                            <p className="font-medium text-white capitalize">
                              {mealType}: {meal.name}
                            </p>
                            <p className="text-gray-400 text-xs">
                              {meal.recipe}
                            </p>
                            <div className="flex gap-2 text-xs text-gray-500 mt-1">
                              {meal.cooking_time && (
                                <span>⏱️ {meal.cooking_time}</span>
                              )}
                              {meal.difficulty && (
                                <span>📊 {meal.difficulty}</span>
                              )}
                              {meal.cost && (
                                <span>💰 ${meal.cost.toFixed(2)}</span>
                              )}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Cooking Tips */}
              {mealPlan.cooking_tips && mealPlan.cooking_tips.length > 0 && (
                <div className="border border-white rounded-lg p-3 bg-black">
                  <h3 className="font-bold text-white mb-2">💡 Cooking Tips</h3>
                  <ul className="space-y-1 text-xs text-gray-300">
                    {mealPlan.cooking_tips.map((tip: string, index: number) => (
                      <li key={index} className="list-disc list-inside">{tip}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Storage Advice */}
              {mealPlan.storage_advice && mealPlan.storage_advice.length > 0 && (
                <div className="border border-white rounded-lg p-3 bg-black">
                  <h3 className="font-bold text-white mb-2">📦 Storage Advice</h3>
                  <ul className="space-y-1 text-xs text-gray-300">
                    {mealPlan.storage_advice.map((advice: string, index: number) => (
                      <li key={index} className="list-disc list-inside">{advice}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
