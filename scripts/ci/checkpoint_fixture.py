"""Tiny isolated Actions transport probe; never produces a Yagua candidate."""
import argparse
import json
import os

from scripts.ci import checkpoints as cp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['seed', 'consume'])
    parser.add_argument('--dependency')
    args = parser.parse_args()
    platform = os.environ['STAGE_PLATFORM']
    if args.mode == 'seed':
        cp.STATE.mkdir()
        fingerprint, inputs = cp.fingerprint('compile', platform, '2.0.0', {})
        cp.output('fingerprint', fingerprint)
        (cp.STATE / 'context.json').write_text(json.dumps({
            'stage': 'compile', 'platform': platform, 'version': '2.0.0', 'lineage': {},
            'fingerprint': fingerprint, 'inputs': inputs}))
        fixture = cp.ROOT / 'dist/fixture'
        fixture.mkdir(parents=True)
        (fixture / 'tool').write_text('tiny fixture')
        (fixture / 'tool').chmod(0o755)
        if platform == 'linux':
            (fixture / 'alias').symlink_to('tool')
        cp.save(['dist/fixture/tool'] + (['dist/fixture/alias'] if platform == 'linux' else []))
    else:
        cp.prepare('package', platform, '2.0.0', {'compile': args.dependency}, '', False)
        assert (cp.ROOT / 'dist/fixture/tool').read_text() == 'tiny fixture'
        if platform == 'linux':
            assert (cp.ROOT / 'dist/fixture/tool').stat().st_mode & 0o111
            assert os.readlink(cp.ROOT / 'dist/fixture/alias') == 'tool'
        print('Tiny checkpoint transport, hashes, provenance and permissions passed.')


if __name__ == '__main__':
    main()
