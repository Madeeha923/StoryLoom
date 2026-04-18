import { useEffect, useRef, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const initialForm = {
  text: "",
};

function App() {
  const [form, setForm] = useState(initialForm);
  const [imageFile, setImageFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [audioPreviewUrl, setAudioPreviewUrl] = useState("");
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [micMessage, setMicMessage] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadResult, setUploadResult] = useState(null);
  const [previewIndex, setPreviewIndex] = useState(0);
  const [isPreviewPlaying, setIsPreviewPlaying] = useState(true);

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const previewUrlRef = useRef("");
  const audioPreviewUrlRef = useRef("");

  useEffect(() => {
    return () => {
      cleanupObjectUrl(previewUrlRef.current);
      cleanupObjectUrl(audioPreviewUrlRef.current);
      stopMediaStream(mediaStreamRef.current);
    };
  }, []);

  useEffect(() => {
    const generatedImages = result?.images || [];
    setPreviewIndex(0);
    setIsPreviewPlaying(true);

    if (!generatedImages.length) {
      return undefined;
    }
  }, [result]);

  useEffect(() => {
    const generatedImages = result?.images || [];
    if (!generatedImages.length || !isPreviewPlaying) {
      return undefined;
    }

    const currentImage = generatedImages[previewIndex] || generatedImages[0];
    const durationSeconds = Number(currentImage?.duration_seconds) || 4;
    const timer = window.setTimeout(() => {
      setPreviewIndex((current) => (current + 1) % generatedImages.length);
    }, durationSeconds * 1000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [result, previewIndex, isPreviewPlaying, videoPreviewUrl]);

  function handleTextChange(event) {
    const { value } = event.target;
    setForm((current) => ({ ...current, text: value }));
  }

  function handleImageChange(event) {
    const file = event.target.files?.[0] || null;
    setImageFile(file);
    replacePreviewUrl(file);
  }

  async function handleMicToggle() {
    if (isRecording) {
      stopRecording();
      return;
    }

    if (
      typeof window === "undefined" ||
      typeof window.MediaRecorder === "undefined" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      setMicMessage("Your browser does not support direct microphone recording.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = resolveRecordingMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      setMicMessage("Recording in progress. Tap again to stop.");
      setError("");

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        audioChunksRef.current = [];
        mediaRecorderRef.current = null;
        stopMediaStream(stream);
        mediaStreamRef.current = null;

        if (!blob.size) {
          setMicMessage("No audio was captured. Please try again.");
          return;
        }

        const extension = blob.type.includes("mp4") ? "m4a" : "webm";
        const recordedFile = new File(
          [blob],
          `storyloom-mic-${Date.now()}.${extension}`,
          { type: blob.type || "audio/webm" }
        );

        setAudioFile(recordedFile);
        replaceAudioPreviewUrl(blob);
        setMicMessage("Voice note captured and ready for transcription.");
      };

      recorder.start();
      setIsRecording(true);
    } catch (recordingError) {
      setMicMessage(
        recordingError?.message ||
          "Microphone access was denied. Please allow mic permission and try again."
      );
      stopMediaStream(mediaStreamRef.current);
      mediaStreamRef.current = null;
      mediaRecorderRef.current = null;
      setIsRecording(false);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }

  function clearRecording() {
    if (isRecording) {
      stopRecording();
    }
    setAudioFile(null);
    cleanupObjectUrl(audioPreviewUrlRef.current);
    audioPreviewUrlRef.current = "";
    setAudioPreviewUrl("");
    setMicMessage("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!imageFile) {
      setError("Upload a product image to begin the StoryLoom workflow.");
      return;
    }

    setError("");
    setUploadMessage("");
    setUploadResult(null);
    setIsLoading(true);
    setResult(null);

    const payload = new FormData();
    payload.append("image", imageFile);
    if (form.text.trim()) {
      payload.append("text", form.text.trim());
    }
    if (audioFile) {
      payload.append("audio", audioFile);
    }
    payload.append("simulated_confirmation_response", "approved");

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/generate-listing`, {
        method: "POST",
        body: payload,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "StoryLoom could not generate the listing.");
      }

      setResult(data);
    } catch (submissionError) {
      setError(submissionError.message || "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUploadToOndc() {
    if (!result?.upload_ready_data || !Object.keys(result.upload_ready_data).length) {
      setUploadMessage("No upload-ready package is available yet.");
      return;
    }

    setIsUploading(true);
    setUploadMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/mock/ondc/catalog/upload`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(result.upload_ready_data),
        }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Upload handoff failed.");
      }

      setUploadResult(data);
      setUploadMessage(
        "StoryLoom triggered the upload handoff successfully. The current integration is a mock ONDC endpoint."
      );
    } catch (uploadError) {
      setUploadMessage(uploadError.message || "Upload handoff failed.");
    } finally {
      setIsUploading(false);
    }
  }

  function handleReset() {
    cleanupObjectUrl(previewUrlRef.current);
    cleanupObjectUrl(audioPreviewUrlRef.current);
    stopMediaStream(mediaStreamRef.current);

    previewUrlRef.current = "";
    audioPreviewUrlRef.current = "";
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];

    setForm(initialForm);
    setImageFile(null);
    setAudioFile(null);
    setPreviewUrl("");
    setAudioPreviewUrl("");
    setResult(null);
    setError("");
    setMicMessage("");
    setUploadMessage("");
      setUploadResult(null);
      setIsRecording(false);
    setPreviewIndex(0);
    setIsPreviewPlaying(true);
  }

  const generatedImages = result?.images || [];
  const uploadReadyData = result?.upload_ready_data || {};
  const stageLogs = result?.stage_logs || [];
  const pipelineErrors = result?.pipeline_errors || [];
  const activePreviewImage =
    generatedImages[previewIndex] || generatedImages[0] || null;
  const totalPreviewDuration = generatedImages.reduce(
    (total, image) => total + (Number(image?.duration_seconds) || 4),
    0
  );

  return (
    <div className="page-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />

      <main className="layout">
        <section className="hero-grid">
          <div className="hero-panel">
            <h1 className="brand-title">StoryLoom</h1>
            <p className="hero-kicker">Upload. Shape. List.</p>
            <p className="hero-text">
              StoryLoom is a workspace for turning one product photo
              into premium listing copy, campaign visuals, a video script, and a
              marketplace-ready upload package.
            </p>
          </div>
        </section>

        <section className="workspace-grid">
          <form className="studio-panel input-panel" onSubmit={handleSubmit}>
            <SectionHeading
              title="Upload Your Product"
              subtitle="Add one product image, enrich the brief, and record a quick spoken note if needed."
            />

            <label className="field">
              <span>Product Image</span>
              <input type="file" accept="image/*" onChange={handleImageChange} />
            </label>

            {previewUrl ? (
              <div className="preview-card">
                <img src={previewUrl} alt="Product preview" />
              </div>
            ) : (
              <div className="preview-card empty-preview">
                <p>Your uploaded product preview will appear here.</p>
              </div>
            )}

            <label className="field">
              <span>Creative Brief</span>
              <textarea
                name="text"
                value={form.text}
                onChange={handleTextChange}
                rows={7}
                placeholder="Describe the product, audience, mood, selling angle, occasion, or styling direction."
              />
            </label>

            <div className="mic-card">
              <div className="mic-head">
                <div>
                  <span className="field-label">Direct Mic</span>
                  <p>
                    Record a short voice note instead of uploading an audio file.
                  </p>
                </div>
                <button
                  className={`mic-button ${isRecording ? "is-recording" : ""}`}
                  type="button"
                  onClick={handleMicToggle}
                >
                  {isRecording ? "Stop Recording" : "Start Mic"}
                </button>
              </div>

              {micMessage ? <p className="mic-message">{micMessage}</p> : null}

              {audioPreviewUrl ? (
                <div className="audio-preview">
                  <audio controls src={audioPreviewUrl} />
                  <button
                    className="secondary-button subtle-button"
                    type="button"
                    onClick={clearRecording}
                  >
                    Clear Voice Note
                  </button>
                </div>
              ) : null}
            </div>

            {error ? <div className="banner error">{error}</div> : null}

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={isLoading}>
                {isLoading ? "Creating Listing..." : "Proceed with StoryLoom"}
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={handleReset}
              >
                Reset Workspace
              </button>
            </div>
          </form>

          <div className="results-column">
            <section className="studio-panel overview-panel">
              <SectionHeading
                title="Generation Overview"
                subtitle="A live view of the listing state, visual output, and final marketplace readiness."
              />

              <div className="metric-grid">
                <MetricCard
                  label="Pipeline"
                  value={result?.pipeline_status || "idle"}
                  tone={result?.pipeline_status || "idle"}
                />
                <MetricCard
                  label="Images"
                  value={generatedImages.length ? `${generatedImages.length} ready` : "waiting"}
                  tone={generatedImages.length ? "success" : "idle"}
                />
                <MetricCard
                  label="Upload"
                  value={result?.ready_for_upload ? "ready" : "pending"}
                  tone={result?.ready_for_upload ? "success" : "partial"}
                />
              </div>
            </section>

            <section className="studio-panel gallery-panel">
              <SectionHeading
                title="Generated Visuals"
                subtitle="Professional campaign images generated from the uploaded product reference."
              />

              <div className="image-gallery">
                {generatedImages.length ? (
                  generatedImages.map((image) => (
                    <figure className="gallery-card" key={image.scene_number}>
                      <img
                        src={resolveImageSrc(image)}
                        alt={image.scene_title || `Scene ${image.scene_number}`}
                      />
                      <figcaption>
                        <strong>{image.scene_title}</strong>
                        <p>{image.scene_description}</p>
                      </figcaption>
                    </figure>
                  ))
                ) : (
                  <EmptyState text="Generated images will appear here after the StoryLoom run completes." />
                )}
              </div>
            </section>

            <section className="studio-panel video-panel">
              <SectionHeading
                title="Campaign Video"
                subtitle="A reliable campaign-style preview that plays through the generated frames in sequence."
              />

              {generatedImages.length ? (
                <div className="fallback-player-card">
                  <img
                    src={resolveImageSrc(activePreviewImage)}
                    alt={
                      activePreviewImage?.scene_title || "Generated preview frame"
                    }
                  />
                  <div className="fallback-player-controls">
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() =>
                        setPreviewIndex((current) =>
                          current === 0 ? generatedImages.length - 1 : current - 1
                        )
                      }
                    >
                      Previous
                    </button>
                    <button
                      className="primary-button"
                      type="button"
                      onClick={() => setIsPreviewPlaying((current) => !current)}
                    >
                      {isPreviewPlaying ? "Pause Video" : "Play Video"}
                    </button>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() =>
                        setPreviewIndex((current) => (current + 1) % generatedImages.length)
                      }
                    >
                      Next
                    </button>
                  </div>

                  <div className="preview-meta">
                    <span>
                      Frame {previewIndex + 1} of {generatedImages.length}
                    </span>
                    <span>{totalPreviewDuration}s total preview</span>
                  </div>

                  <div className="preview-timeline">
                    {generatedImages.map((image, index) => (
                      <button
                        key={`${image.scene_number}-${index}`}
                        type="button"
                        className={`timeline-segment ${
                          index === previewIndex ? "is-active" : ""
                        }`}
                        onClick={() => setPreviewIndex(index)}
                        aria-label={`Go to frame ${index + 1}`}
                      />
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState
                  text="The campaign video preview will appear here after image generation."
                />
              )}
            </section>

            <section className="studio-panel narrative-panel">
              <SectionHeading
                title={result?.product_title || "Listing Narrative"}
                subtitle="Your product story and ad script are arranged side by side for a cleaner review."
              />

              <div className="copy-grid">
                <article className="copy-card">
                  <span className="copy-label">Product Description</span>
                  <p>
                    {result?.product_description ||
                      "The generated product description will appear here as a polished paragraph."}
                  </p>
                </article>

                <article className="copy-card">
                  <span className="copy-label">Video Script</span>
                  <p>
                    {result?.video_script ||
                      "The short ad script will appear here after the campaign is generated."}
                  </p>
                </article>
              </div>
            </section>

            <section className="studio-panel upload-panel">
              <SectionHeading
                title="Final Upload"
                subtitle="Trigger the Registrar handoff to the ONDC-style upload endpoint after reviewing the generated listing."
              />

              <div className="upload-cta">
                <div className="upload-copy">
                  <h3>Send Listing to ONDC Flow</h3>
                  <p>
                    This button triggers the upload package produced by the
                    agents. The current integration is a mock ONDC endpoint, so
                    you can test the final handoff safely before live rollout.
                  </p>
                </div>

                <button
                  className="primary-button upload-button"
                  type="button"
                  disabled={isUploading || !result?.ready_for_upload}
                  onClick={handleUploadToOndc}
                >
                  {isUploading ? "Uploading..." : "Upload to ONDC"}
                </button>
              </div>

              {uploadMessage ? (
                <div className="banner successish">{uploadMessage}</div>
              ) : null}

              {uploadResult ? (
                <div className="upload-result">
                  <div>
                    <span className="detail-label">Status</span>
                    <p>{uploadResult.status}</p>
                  </div>
                  <div>
                    <span className="detail-label">Reference</span>
                    <p>{uploadResult.submission_reference}</p>
                  </div>
                </div>
              ) : null}
            </section>

            <section className="studio-panel technical-panel">
              <details>
                <summary className="details-summary">
                  Technical Details
                </summary>

                <div className="technical-grid">
                  <div className="technical-block">
                    <h3>Upload Package</h3>
                    <pre className="json-viewer">
                      {JSON.stringify(uploadReadyData, null, 2) || "{}"}
                    </pre>
                  </div>

                  <div className="technical-block">
                    <h3>Pipeline Logs</h3>
                    <div className="log-list">
                      {stageLogs.length ? (
                        stageLogs.map((log, index) => (
                          <div className="log-item" key={`${log.stage}-${index}`}>
                            <strong>{log.stage}</strong>
                            <span>
                              {log.event} / {log.status}
                            </span>
                            <small>{log.duration_ms} ms</small>
                          </div>
                        ))
                      ) : (
                        <EmptyState text="Stage logs will appear here." />
                      )}
                    </div>

                    <h3 className="error-title">Pipeline Errors</h3>
                    <div className="log-list">
                      {pipelineErrors.length ? (
                        pipelineErrors.map((item, index) => (
                          <div
                            className="log-item error-item"
                            key={`${item.stage}-${index}`}
                          >
                            <strong>{item.stage}</strong>
                            <span>{item.message}</span>
                            <small>{item.status}</small>
                          </div>
                        ))
                      ) : (
                        <EmptyState text="No pipeline errors reported." />
                      )}
                    </div>
                  </div>
                </div>
              </details>
            </section>
          </div>
        </section>
      </main>
    </div>
  );

  function replacePreviewUrl(file) {
    cleanupObjectUrl(previewUrlRef.current);
    const nextUrl = file ? URL.createObjectURL(file) : "";
    previewUrlRef.current = nextUrl;
    setPreviewUrl(nextUrl);
  }

  function replaceAudioPreviewUrl(blob) {
    cleanupObjectUrl(audioPreviewUrlRef.current);
    const nextUrl = blob ? URL.createObjectURL(blob) : "";
    audioPreviewUrlRef.current = nextUrl;
    setAudioPreviewUrl(nextUrl);
  }
}

function resolveRecordingMimeType() {
  if (
    typeof window !== "undefined" &&
    window.MediaRecorder &&
    window.MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
  ) {
    return "audio/webm;codecs=opus";
  }

  if (
    typeof window !== "undefined" &&
    window.MediaRecorder &&
    window.MediaRecorder.isTypeSupported("audio/webm")
  ) {
    return "audio/webm";
  }

  return "";
}

function wait(durationMs) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, durationMs);
  });
}

function cleanupObjectUrl(url) {
  if (url) {
    URL.revokeObjectURL(url);
  }
}

function stopMediaStream(stream) {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
}

function resolveImageSrc(image) {
  const imageUrl = String(image?.image_url || "").trim();
  if (imageUrl) {
    return imageUrl.startsWith("http") ? imageUrl : `${API_BASE_URL}${imageUrl}`;
  }

  const imageBase64 = String(image?.frame_image_b64 || "").trim();
  return imageBase64 ? `data:image/png;base64,${imageBase64}` : "";
}

function SectionHeading({ title, subtitle }) {
  return (
    <div className="section-heading">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>
  );
}

function MetricCard({ label, value, tone }) {
  return (
    <div className={`metric-tile tone-${tone || "idle"}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>;
}

export default App;
