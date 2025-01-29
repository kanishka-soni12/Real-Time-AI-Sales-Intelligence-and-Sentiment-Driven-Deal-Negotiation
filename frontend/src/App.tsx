import React, { useState, useRef } from 'react';
import './App.css';

interface CustomerData {
  customer_name: string;
  email: string;
  last_purchase_date: string;
  purchase_history: number;
  customer_segment: string;
  interaction_history: string[];
}

const API_BASE_URL = 'http://localhost:8000';

const Recommendations = ({ phoneNumber }: { phoneNumber: string }) => {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/get-recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="recommendations-container">
      <h3>Negotiation Recommendations</h3>
      <button onClick={fetchRecommendations} disabled={isLoading}>
        Get Recommendations
      </button>
      
      {isLoading && <p>Loading recommendations...</p>}
      
      {recommendations.length > 0 && (
        <ul>
          {recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

const PostCallAnalysis = ({ phoneNumber }: { phoneNumber: string }) => {
  const [postCallAnalysis, setPostCallAnalysis] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchPostCallAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/post-call-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch post-call analysis');
      }

      const data = await response.json();
      setPostCallAnalysis(data.post_call_analysis);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to retrieve post-call analysis');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="post-call-analysis-container">
      <h3>Post Call Analysis</h3>
      <button onClick={fetchPostCallAnalysis} disabled={isLoading}>
        Get Post Call Analysis
      </button>
      
      {isLoading && <p>Loading post-call analysis...</p>}
      
      {postCallAnalysis && (
        <div className="post-call-analysis-result">
          <pre>{postCallAnalysis}</pre>
        </div>
      )}
    </div>
  );
};

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [analysis, setAnalysis] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [customerData, setCustomerData] = useState<CustomerData | null>(null);
  const [lookupError, setLookupError] = useState('');

  // Ref to store recognition instance
  const recognitionRef = useRef<any>(null);
  // Ref to accumulate transcription
  const transcriptionAccumulatorRef = useRef('');

  const lookupCustomer = async () => {
    setLookupError('');
    setCustomerData(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/lookup-customer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Customer not found');
      }

      setCustomerData(data);
    } catch (error) {
      console.error('Lookup error:', error);
      setLookupError(error instanceof Error ? error.message : 'Error looking up customer');
      setCustomerData(null);
    }
  };

  const startRecording = async () => {
    if (!customerData) {
      alert('Please lookup customer first');
      return;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('Your browser does not support speech recognition. Please use Google Chrome.');
        return;
      }

      // Reset accumulated transcription
      transcriptionAccumulatorRef.current = '';
      setTranscription('');
      setAnalysis('');

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      
      recognition.lang = 'en-US';
      recognition.continuous = true;  // Continuous recording
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        // Accumulate final transcripts
        transcriptionAccumulatorRef.current += finalTranscript;
        setTranscription(transcriptionAccumulatorRef.current);
      };

      recognition.onend = async () => {
        // If still supposed to be recording, restart
        if (isRecording) {
          recognition.start();
        } else {
          // Process final transcription when stopped
          await processFinalTranscription();
        }
      };

      recognition.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error during speech recording:', error);
      alert('Error starting speech recognition.');
    }
  };

  const processFinalTranscription = async () => {
    if (!transcriptionAccumulatorRef.current) return;

    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/analyze-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text_data: transcriptionAccumulatorRef.current,
          phone_number: phoneNumber,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data.analysis);
    } catch (error) {
      console.error('Error sending transcription to backend:', error);
      alert('Error analyzing speech.');
    } finally {
      setIsProcessing(false);
    }
  };

  const stopRecording = () => {
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="app-container">
      <h1>AI Sales Assistant V4</h1>
      
      <div className="customer-lookup">
        <input
          type="text"
          placeholder="Enter phone number"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          className="phone-input"
        />
        <button onClick={lookupCustomer} className="lookup-button">
          Lookup Customer
        </button>
      </div>

      {lookupError && (
        <div className="error-message">
          {lookupError}
        </div>
      )}

      {customerData && (
        <>
          <div className="customer-info">
            <h2>Customer Details</h2>
            <p><strong>Name:</strong> {customerData.customer_name}</p>
            <p><strong>Email:</strong> {customerData.email}</p>
            <p><strong>Last Purchase:</strong> {customerData.last_purchase_date}</p>
            <p><strong>Purchase History:</strong> ${customerData.purchase_history}</p>
            <p><strong>Segment:</strong> {customerData.customer_segment}</p>
            
            {customerData.interaction_history && customerData.interaction_history.length > 0 && (
              <div className="interaction-history">
                <h3>Previous Interactions</h3>
                <ul>
                  {customerData.interaction_history.map((interaction, index) => (
                    <li key={index}>{interaction}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <div className="control-panel">
            <button 
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'stop' : 'start'}
              disabled={isProcessing || !customerData}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            
            {isProcessing && <div className="processing">Processing...</div>}
            {isRecording && <div className="recording">Recording...</div>}
          </div>

          {transcription && (
            <div className="result-box">
              <h2>Transcription:</h2>
              <p>{transcription}</p>
            </div>
          )}
          
          {analysis && (
            <div className="result-box">
              <h2>Analysis</h2>
              <pre>{analysis}</pre>
            </div>
          )}
          
          <Recommendations phoneNumber={phoneNumber} />
          <PostCallAnalysis phoneNumber={phoneNumber} />
        </>
      )}
    </div>
  );
}

export default App;