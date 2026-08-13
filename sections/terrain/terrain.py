import bmesh


def generate_grid(
    bm: bmesh.types.BMesh,
    grid_points_x: int,
    grid_points_y: int,
    grid_size_x: float,
    grid_size_y: float,
) -> None:
    bmesh.ops.create_grid(
        bm,
        x_segments=grid_points_x,
        y_segments=grid_points_y,
        size=grid_size_x,
    )
