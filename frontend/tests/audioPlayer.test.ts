import getAudioPlayer from '../components/audioPlayer.js';

describe('audioPlayer singleton', () => {
  test('reuses existing #audio-player element', () => {
    const existing = document.createElement('audio');
    existing.id = 'audio-player';
    document.body.appendChild(existing);

    const player1 = getAudioPlayer();
    expect(player1).toBe(existing);
    const player2 = getAudioPlayer();
    expect(player2).toBe(existing);
  });

  test('creates element when missing', () => {
    const found = document.getElementById('audio-player');
    if (found) found.remove();

    const player = getAudioPlayer();
    expect(player.id).toBe('audio-player');
    expect(document.getElementById('audio-player')).toBe(player);
  });
});
