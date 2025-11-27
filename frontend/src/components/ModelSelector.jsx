import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Typography,
  Box,
  Chip,
  Divider,
  TextField,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RestartAltIcon from '@mui/icons-material/RestartAlt';

// Default prompts for each model
const DEFAULT_PROMPTS = {
  qwen2vl: "Describe what you see in this video, including actions, objects, and any visible text on screen.",
  omnivinci: "Describe this video including both visual content and audio track. Mention any speech, music, sounds, or audio details you detect.",
  qwen3omni: "Analyze this video comprehensively. Describe the visual content, audio elements, context, and explain the meaning or story. Include detailed reasoning about what's happening and why.",
  qwen3omni_captioner: "Audio-only captioning model - no prompt needed (prompt is ignored)."
};

const ModelSelector = ({ open, onClose, onSelect, models, defaultModel }) => {
  const [selectedModel, setSelectedModel] = React.useState(defaultModel || 'qwen2vl');
  const [customPrompt, setCustomPrompt] = React.useState(DEFAULT_PROMPTS[defaultModel || 'qwen2vl']);

  // Update prompt when model changes
  React.useEffect(() => {
    if (selectedModel) {
      setCustomPrompt(DEFAULT_PROMPTS[selectedModel] || '');
    }
  }, [selectedModel]);

  React.useEffect(() => {
    if (defaultModel) {
      setSelectedModel(defaultModel);
      setCustomPrompt(DEFAULT_PROMPTS[defaultModel] || '');
    }
  }, [defaultModel]);

  const handleSelect = () => {
    onSelect(selectedModel, customPrompt);  // Pass both model and prompt
    onClose();
  };

  const handleResetPrompt = () => {
    setCustomPrompt(DEFAULT_PROMPTS[selectedModel] || '');
  };

  const getModelInfo = (key) => {
    if (!models || !models[key]) return null;
    return models[key];
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h6">Select AI Model</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Choose which model to use for caption generation
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <RadioGroup
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
        >
          {/* Dynamically render all available models */}
          {models && Object.keys(models).map((modelKey, index) => {
            const modelInfo = models[modelKey];
            const isDefault = modelKey === defaultModel;
            
            return (
              <React.Fragment key={modelKey}>
                <FormControlLabel
                  value={modelKey}
                  control={<Radio />}
                  label={
                    <Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1">
                          {modelInfo?.display_name || modelKey}
                        </Typography>
                        <Chip
                          label="Apache 2.0"
                          size="small"
                          color="success"
                          icon={<CheckCircleIcon />}
                        />
                        {isDefault && (
                          <Chip label="Default" size="small" color="primary" variant="outlined" />
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                        {modelKey === 'qwen2vl' && '7B parameters • Fast • Lightweight • Via vLLM'}
                        {modelKey === 'omnivinci' && '9B parameters • Vision+Audio+Text • NVIDIA • Via Transformers'}
                        {modelKey === 'qwen3omni' && '30B parameters • Thinking capability • Vision+Audio+Text'}
                        {modelKey === 'qwen3omni_captioner' && '30B parameters • Audio-only • Fine-grained audio captioning • No prompts needed'}
                      </Typography>
                    </Box>
                  }
                  sx={{ py: 1.5, alignItems: 'flex-start' }}
                />
                {index < Object.keys(models).length - 1 && <Divider sx={{ my: 1 }} />}
              </React.Fragment>
            );
          })}
        </RadioGroup>

        <Box mt={3} p={2} sx={{ backgroundColor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Tip:</strong> All models have Apache 2.0 license (commercial-friendly).
            Qwen2-VL is fastest. OmniVinci adds audio. Qwen3-Omni has thinking capability.
            Qwen3-Omni-Captioner is audio-only and generates fine-grained audio descriptions.
          </Typography>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Prompt Customization */}
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Prompt (Customize what the AI analyzes)
            </Typography>
            <Button
              size="small"
              startIcon={<RestartAltIcon />}
              onClick={handleResetPrompt}
            >
              Reset to Default
            </Button>
          </Box>
          <TextField
            multiline
            rows={4}
            fullWidth
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder={DEFAULT_PROMPTS[selectedModel]}
            variant="outlined"
            disabled={selectedModel === 'qwen3omni_captioner'}
            helperText={
              selectedModel === 'qwen3omni_captioner' 
                ? "This model is audio-only and does not accept text prompts. Audio will be automatically extracted from the video."
                : "Edit to focus on specific aspects (actions, audio, text, emotions, etc.)"
            }
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSelect} variant="contained" autoFocus>
          Generate Caption
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ModelSelector;

