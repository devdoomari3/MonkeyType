from mypy_extensions import TypedDict

Nested = TypedDict(
    'Nested',
    {
        'child1': int,
    }
)

Movie = TypedDict(
    'Movie', {
        'name': str, 'year': int,
        'nested': Nested,
    })



Movie2 = TypedDict('Movie2', {'name': str, 'year': int})

def test(a: Movie) -> None:
    print(a)

some_movie: Movie = {
    'name': 'movie-name',
    'year': 199,
    'nested': {
        'child1': 1,
    }
}
