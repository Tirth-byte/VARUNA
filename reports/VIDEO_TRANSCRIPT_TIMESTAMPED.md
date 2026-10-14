# VARUNA Final Video — Timestamped Transcript

Source: `/Users/macbookair/Desktop/VARUNA.mp4`  
Duration: **00:03:49.600**  
Method: mono 16 kHz PCM extraction from the complete AAC stream, followed by `faster-whisper` (`small.en`, beam size 5). Timestamps were checked against the video timeline. Minor punctuation and obvious ASR slips were normalized; wording was otherwise preserved.

| Start | End | Transcript |
|---:|---:|---|
| 00:00.000 | 00:11.940 | Hi everyone, so this is VARUNA. The name comes from the ancient Vedic god associated with water, and the idea behind it is pretty simple. |
| 00:12.320 | 00:20.720 | When floods happen, we often don't know exactly what changes on the ground, especially in mountain areas where reaching places can be difficult. |
| 00:21.200 | 00:25.760 | So we thought, why not use satellites to help us understand that? And that's how VARUNA started. |
| 00:26.460 | 00:35.140 | So let me show you how it works. For this project, we have used real Sentinel-1 satellite data from the floods in Nepal in August 2026. |
| 00:35.840 | 00:42.380 | This is the image which is showing two parts. One is before the flood and one is after the flood. |
| 00:44.260 | 00:49.520 | And that's the cool thing about radar satellites: they can see through clouds. |
| 00:50.520 | 01:02.300 | Now when I turn on the highlights, you can see two colors. If I zoom in on the after part, you will be able to see two colors. |
| 01:04.920 | 01:12.560 | One is blue and one is yellow. So the blue means the radar signal has decreased, which can indicate water. |
| 01:13.140 | 01:18.340 | And orange means it has increased, which could be debris or other changes on the ground. |
| 01:18.340 | 01:26.540 | So instead of just looking at two images, we can actually start understanding what changed before and after. |
| 01:28.940 | 01:34.420 | Here VARUNA analyzed those changes and highlighted possible flood areas and debris. |
| 01:34.860 | 01:41.840 | For our case study, we found 126 square kilometers of possible floodwater in raw results. |
| 01:41.840 | 01:48.820 | Of course, these are satellite-based estimates, not confirmed damage, but they give us a useful starting point. |
| 01:50.160 | 01:56.260 | Now finding water is one thing, but what really matters is how it affects people. |
| 01:56.700 | 02:01.960 | So we added OpenStreetMap data to see which buildings and roads might be affected. |
| 02:02.380 | 02:09.820 | In our analysis, around 1,062 buildings and 35 kilometers of road overlap with possible hazard areas. |
| 02:09.820 | 02:18.200 | We also built a road-network analysis to check which communities might lose access to important places like hospitals. |
| 02:18.760 | 02:26.640 | In our modeled scenario, six settlements could become disconnected if certain roads are blocked. |
| 02:30.540 | 02:39.580 | Now, when comparing with Copernicus Emergency Management Service, we found around 37% spatial overlap in our reference area. |
| 02:39.580 | 02:45.600 | It's not an accuracy percentage, but it helps us understand how our results compare with another source. |
| 02:47.760 | 02:50.620 | Now we also added an AI copilot. |
| 02:52.580 | 02:58.060 | You can ask questions about the flood, the roads, or affected areas in English or Nepali. |
| 02:59.220 | 03:00.620 | And it will give you the answers. |
| 03:02.120 | 03:06.720 | We give both access because rural people can also use it. |
| 03:10.580 | 03:13.960 | Then we have reports and a research report. |
| 03:16.160 | 03:19.720 | So finally VARUNA generates two reports: |
| 03:20.620 | 03:34.320 | A one-page situation report for quick overview, and a research report explaining our methods, results, and limitations. |
| 03:34.320 | 03:42.180 | So yeah, that's VARUNA. We are trying to make satellite data easier to understand and more useful when disasters happen. |
| 03:42.580 | 03:46.760 | Because when we can't reach the ground, we can still look from space. |
| 03:48.040 | 03:48.720 | Thank you. |

## Transcription notes

- The spoken track is English; a Nepali **UI response** appears visually, but no Nepali speech is heard.
- ASR confidence identified English with probability 1.0. “Vedic gold,” “moded,” and “spiral overlap” in raw ASR were corrected from context to “Vedic god,” “modeled,” and “spatial overlap.”
- Silence/gaps between phrases are retained in the timestamps.
