from hypothesis.strategies import integers, just, fixed_dictionaries, none, lists, text, sampled_from

from githooks.utils import get_hook_names


def api_results(min_size=0, max_size=20, hook_types=None):
    count = integers(min_value=min_size, max_value=max_size).example()
    hook_types = hook_types or get_hook_names()

    return fixed_dictionaries({
        'count': just(count),
        'next': none(),
        'prev': none(),
        'results': lists(fixed_dictionaries({
            'name': text(min_size=1),
            'latest_version': integers(min_value=0),
            'content': fixed_dictionaries({
                "hook_type": sampled_from(hook_types),
                "version": integers(min_value=0),
                "description": text(min_size=1),
                "download_url": text(min_size=1),
                "checksum": text(min_size=1),
            })
        }), min_size=count, max_size=count)
    })
