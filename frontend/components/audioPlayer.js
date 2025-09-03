const getAudioPlayer = (() => {
  let player;
  return () => {
    if (!player) {
      player = document.getElementById('audio-player');
      if (!player) {
        player = document.createElement('audio');
        player.id = 'audio-player';
        document.body.appendChild(player);
      }
    }
    return player;
  };
})();

export default getAudioPlayer;
