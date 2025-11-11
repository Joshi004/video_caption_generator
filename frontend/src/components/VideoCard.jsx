import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  Stack,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AudioFileIcon from '@mui/icons-material/AudioFile';

const VideoCard = ({ video, onGenerateCaption, onViewCaption, onGenerateAudio }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'Unknown';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
          <Typography
            variant="h6"
            component="div"
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              flex: 1,
            }}
          >
            {video.filename}
          </Typography>
          <Box display="flex" gap={0.5} flexShrink={0}>
            <Chip
              label={video.has_caption ? 'Captioned' : 'No Caption'}
              color={video.has_caption ? 'success' : 'warning'}
              size="small"
            />
            {video.has_audio && (
              <Chip
                label="Audio"
                color="info"
                size="small"
                icon={<AudioFileIcon />}
              />
            )}
          </Box>
        </Box>

        <Stack spacing={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="text.secondary">
              Size:
            </Typography>
            <Typography variant="body2">
              {formatFileSize(video.size)}
            </Typography>
          </Box>

          {video.duration && (
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="text.secondary">
                Duration:
              </Typography>
              <Typography variant="body2">
                {formatDuration(video.duration)}
              </Typography>
            </Box>
          )}

          {video.model_used && (
            <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
              <Typography variant="body2" color="text.secondary">
                Model{video.model_used.includes(',') ? 's' : ''}:
              </Typography>
              {video.model_used.split(',').map((model, idx) => (
                <Chip
                  key={idx}
                  label={model.trim().toUpperCase()}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
              ))}
            </Box>
          )}
        </Stack>

        {video.has_caption && video.caption_text && (
          <Box
            mt={2}
            p={1.5}
            sx={{
              backgroundColor: 'grey.50',
              borderRadius: 1,
              maxHeight: 80,
              overflow: 'hidden',
            }}
          >
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {video.caption_text}
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ p: 2, pt: 0 }}>
        <Stack direction="column" spacing={1} width="100%">
          <Stack direction="row" spacing={1} width="100%">
            {!video.has_caption ? (
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => onGenerateCaption(video.filename)}
              >
                Generate Caption
              </Button>
            ) : (
              <Button
                fullWidth
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => onGenerateCaption(video.filename, true)}
              >
                Regenerate
              </Button>
            )}
            <Button
              fullWidth
              variant="contained"
              startIcon={<VisibilityIcon />}
              onClick={() => onViewCaption(video)}
            >
              {video.has_caption ? 'View' : 'Play'}
            </Button>
          </Stack>
          {!video.has_audio && onGenerateAudio && (
            <Button
              fullWidth
              variant="outlined"
              color="secondary"
              startIcon={<AudioFileIcon />}
              onClick={() => onGenerateAudio(video.filename)}
            >
              Generate Audio
            </Button>
          )}
        </Stack>
      </CardActions>
    </Card>
  );
};

export default VideoCard;

