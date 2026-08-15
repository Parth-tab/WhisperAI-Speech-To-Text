# Boot-Only Hardware Discovery

To prevent Python Global Interpreter Lock (GIL) deadlocks caused by heavy C-library calls in `sounddevice` and `PortAudio` (`Pa_Initialize`, `Pa_Terminate`), audio recording device enumeration and Bluetooth profile matching occur strictly once at application boot and are cached in memory.
