let instance;

/**
 * Retrieve a shared `<audio>` element.
 *
 * The function looks for an existing element with the id `audio-player`.
 * If found, that element is reused; otherwise a new element is created and
 * appended to the document body. Subsequent calls return the same element.
 */
const getAudioPlayer = () => {
  // Reuse the memoized instance if it still exists in the DOM
  if (instance && document.body.contains(instance)) {
    return instance;
  }

  // Attempt to find an existing element in the DOM
  instance = document.getElementById('audio-player');
  if (!instance) {
    instance = document.createElement('audio');
    instance.id = 'audio-player';
    document.body.appendChild(instance);
  }

  return instance;
};

export default getAudioPlayer;

