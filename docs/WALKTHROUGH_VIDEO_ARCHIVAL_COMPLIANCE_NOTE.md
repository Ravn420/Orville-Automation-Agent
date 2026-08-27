# Walkthrough-Video Archival Compliance Note

**Project:** Orville Automation Agent  
**Control area:** Release evidence and artifact retention  
**Status:** Open — archival evidence incomplete  
**Review date:** 2026-08-28  
**Owner:** Release evidence owner to be assigned

## Finding

The release documentation states that a fallback walkthrough video was rendered at `/home/ubuntu/orville-runs-walkthrough.mp4`, reportedly as a 30-second, 1280×720 H.264 artifact. During the retention review, that path was absent. A read-only search under `/home/ubuntu`, `/tmp`, and `/var/tmp` found no matching walkthrough, recording, or common video file. No repository copy, checksum manifest, delivery record, or archival metadata was found.

The claim is therefore **not currently verifiable from retained evidence**. This is an evidence-retention gap, not a claim that the video was never generated.

## Impact and disposition

The regression release gate remains clear at 788 passed tests with one non-blocking deprecation warning. The missing video does not invalidate the automated test result, but it prevents closure of the walkthrough-artifact retention control and reduces the reproducibility of the visual demonstration.

The related TODO item, `TODO-f8a70d13fc97`, must remain open until one of the closure paths below is completed. The missing artifact must not be silently removed from the task record or represented as archived without a verifiable file and checksum.

## Evidence searched

The review covered the documented absolute path, repository files, sandbox workspace files, common temporary directories, video extensions including MP4, MOV, WebM, and MKV, and archive/manifest/delivery filenames. The review did not print or inspect browser-session contents or other sensitive state.

## Required closure path

The release evidence owner must either:

1. provide the original walkthrough video and archive it in the approved artifact store; or
2. regenerate an equivalent walkthrough under the approved retention procedure; or
3. obtain an explicit waiver from the release owner documenting that the video is unavailable and that the automated release evidence is the accepted substitute.

For either of the first two paths, retain the video with its SHA-256 checksum, file size, media metadata, creation timestamp, source commit, rendering command or capture procedure, reviewer, and archive URI. Verify that the archived object can be downloaded and played before marking the item complete.

For the waiver path, record the approver, decision date, reason for unavailability, replacement evidence, risk acceptance, and expiry or review date. The TODO item should then be closed as **waived**, not as archived.

## Prohibited actions

Do not claim archival completion based solely on the historical TODO narrative. Do not delete or overwrite any similarly named future artifact. Do not upload the video to an external location without an approved destination and a documented retention owner.

## Acceptance criteria

This note may be closed only when the artifact or waiver is linked from the project state record, the checksum or approval evidence is retained, the walkthrough status is reflected consistently in `TODO.md`, `STATE.md`, and the readiness report, and a reviewer confirms the evidence.
