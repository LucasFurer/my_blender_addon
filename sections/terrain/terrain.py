import bmesh
from mathutils import Vector, noise
import math
import random


def generate_grid(
    bm: bmesh.types.BMesh,
    grid_points_x: int,
    grid_points_y: int,
) -> None:

    width_x = grid_points_x - 1
    width_y = grid_points_y - 1

    verts: list[bmesh.types.BMVert] = []

    for y in range(grid_points_y):
        for x in range(grid_points_x):
            verts.append(bm.verts.new((x, y, 0.0)))

    bm.verts.index_update()

    def vert_at(x: int, y: int) -> bmesh.types.BMVert:
        return verts[y * grid_points_x + x]

    for y in range(grid_points_y - 1):
        for x in range(grid_points_x - 1):
            bm.faces.new(
                (
                    vert_at(x, y),
                    vert_at(x + 1, y),
                    vert_at(x + 1, y + 1),
                    vert_at(x, y + 1),
                )
            )

    bm.normal_update()


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


def apply_heightmap_noise(
    bm: bmesh.types.BMesh,
    noise_scale: float,
    noise_height: float,
    layer_amount: int,
    offset_x: float,
    offset_y: float,
) -> None:
    for v in bm.verts:
        current_scale = noise_scale
        current_height = noise_height

        for i in range(layer_amount):
            sample_pos = Vector(
                (
                    (v.co.x + offset_x) * current_scale,
                    (v.co.y + offset_y) * current_scale,
                    0.0,
                )
            )
            v.co.z += noise.noise(sample_pos) * current_height

            current_scale *= 2
            current_height *= 0.5


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


def create_debug_orb_bmesh(
    x: float, y: float, z: float, radius: float = 0.3
) -> bmesh.types.BMesh:
    orb_bm = bmesh.new()
    bmesh.ops.create_uvsphere(orb_bm, u_segments=8, v_segments=8, radius=radius)
    bmesh.ops.translate(orb_bm, verts=orb_bm.verts, vec=(x, y, z))
    return orb_bm


def get_height(
    bm: bmesh.types.BMesh,
    x: int,
    y: int,
    grid_points_x: int,
) -> float:
    return bm.verts[y * grid_points_x + x].co.z


def get_height_interpolate(
    bm: bmesh.types.BMesh,
    x: float,
    y: float,
    grid_points_x: int,
) -> float:
    # grid position of lowest point
    x_l = int(x)
    y_l = int(y)

    # position relative to lowest point
    u = x - float(x_l)
    v = y - float(y_l)

    # heights of the four surrounding corners
    z00 = bm.verts[y_l * grid_points_x + x_l].co.z  # (x_l,   y_l)
    z10 = bm.verts[y_l * grid_points_x + x_l + 1].co.z  # (x_l+1, y_l)
    z01 = bm.verts[(y_l + 1) * grid_points_x + x_l].co.z  # (x_l,   y_l+1)
    z11 = bm.verts[(y_l + 1) * grid_points_x + x_l + 1].co.z  # (x_l+1, y_l+1)

    # bilinear interpolation of the height of the neighbors
    return z00 * (1 - u) * (1 - v) + z10 * u * (1 - v) + z01 * (1 - u) * v + z11 * u * v


def give_sediment(
    bm: bmesh.types.BMesh,
    grid_points_x: int,
    sediment_to_deposit: float,
    d_pos_x: float,
    d_pos_y: float,
) -> None:
    x_l = int(d_pos_x)
    y_l = int(d_pos_y)

    u = d_pos_x - float(x_l)
    v = d_pos_y - float(y_l)

    bm.verts[y_l * grid_points_x + x_l].co.z += (1 - u) * (1 - v) * sediment_to_deposit
    bm.verts[y_l * grid_points_x + x_l + 1].co.z += u * (1 - v) * sediment_to_deposit
    bm.verts[(y_l + 1) * grid_points_x + x_l].co.z += (1 - u) * v * sediment_to_deposit
    bm.verts[(y_l + 1) * grid_points_x + x_l + 1].co.z += u * v * sediment_to_deposit


def take_sediment(
    bm: bmesh.types.BMesh,
    grid_points_x: int,
    grid_points_y: int,
    p_radius: float,
    sediment_to_take: float,
    d_pos_x: float,
    d_pos_y: float,
) -> None:
    x_l = int(d_pos_x)
    y_l = int(d_pos_y)
    discrete_radius = int(p_radius)

    search_min_x = x_l - discrete_radius
    search_min_y = y_l - discrete_radius
    search_max_x = x_l + 1 + discrete_radius
    search_max_y = y_l + 1 + discrete_radius

    norm = 0
    for search_x in range(search_min_x, search_max_x + 1):
        if search_x >= 0 and search_x < grid_points_x:
            for search_y in range(search_min_y, search_max_y + 1):
                if search_y >= 0 and search_y < grid_points_y:
                    diff_x = float(search_x) - d_pos_x
                    diff_y = float(search_y) - d_pos_y

                    norm += max(
                        0.0, p_radius - math.sqrt(diff_x * diff_x + diff_y * diff_y)
                    )

    for search_x in range(search_min_x, search_max_x + 1):
        if search_x >= 0 and search_x < grid_points_x:
            for search_y in range(search_min_y, search_max_y + 1):
                if search_y >= 0 and search_y < grid_points_y:
                    diff_x = float(search_x) - d_pos_x
                    diff_y = float(search_y) - d_pos_y

                    w_i = (
                        max(
                            0.0, p_radius - math.sqrt(diff_x * diff_x + diff_y * diff_y)
                        )
                        / norm
                    )
                    # normally i would use erosion factor (x,y,z) -> [0-1] to decrease the amount that is taken from the gridpoint
                    bm.verts[search_y * grid_points_x + search_x].co.z -= (
                        w_i * sediment_to_take
                    )


def erosion_simulation(
    bm: bmesh.types.BMesh,
    grid_points_x: int,
    grid_points_y: int,
    debug_bmeshes: list[bmesh.types.BMesh],
) -> None:
    bm.verts.ensure_lookup_table()

    # helper variables
    grid_len_x = grid_points_x - 1
    grid_len_y = grid_points_y - 1

    # simulation parameters
    # how many droplets to simulate [1000-x]
    iteration_amount = 50000
    # how many steps each droplet takes [40-x]
    p_maxpath = 30
    # how willing the vel is to change [0-1]
    p_inertia = 0.3
    # the capacity of a water droplet [0-x]
    p_capacity = 8  # 16
    # this is used to erode flatter terrain too
    p_minslope = 0.01  # 0.01
    # gravity makes the points faster [0-x]
    p_gravity = 10  # 10
    # how much water evaporates each step [0-1]
    p_evaporation = 0.02  # 0.025
    # take sediment from points within this distance [math.sqrt(0.5)-x]
    p_radius = 3.0
    # what fraction of the remaining capacity a drop can take from the map [0-1]
    p_erosion = 0.3  # 0.1
    # what fraction of the surplus sediment a drop can place on the map [0-1]
    p_deposition = 0.1  # 0.1

    # repeat for every droplet
    for iter in range(iteration_amount):
        # find starting point for droplet
        d_pos_old_x = random.uniform(0.0, grid_len_x)
        d_pos_old_y = random.uniform(0.0, grid_len_y)

        d_dir_old_x = 0.0
        d_dir_old_y = 0.0

        d_cap = 0.0
        d_water = 1.0
        d_vel = 0.0
        d_sediment = 0.0

        # start moving the droplet
        for move_counter in range(p_maxpath):
            # draw a point
            # point_z = get_height_interpolate(
            #    bm, d_pos_old_x, d_pos_old_y, grid_points_x
            # )
            # debug_bmeshes.append(
            #    create_debug_orb_bmesh(d_pos_old_x, d_pos_old_y, point_z)
            # )

            # grid position of lowest point
            x = int(d_pos_old_x)
            y = int(d_pos_old_y)

            # position relative to lowest point
            u = d_pos_old_x - float(x)
            v = d_pos_old_y - float(y)

            # calculate gradient of neighbor grid points and do bilinear interpolation
            g_d_pos_old_x = (
                get_height(bm, x + 1, y, grid_points_x)
                - get_height(bm, x, y, grid_points_x)
            ) * (1 - v) + (
                get_height(bm, x + 1, y + 1, grid_points_x)
                - get_height(bm, x, y + 1, grid_points_x)
            ) * v
            g_d_pos_old_y = (
                get_height(bm, x, y + 1, grid_points_x)
                - get_height(bm, x, y, grid_points_x)
            ) * (1 - u) + (
                get_height(bm, x + 1, y + 1, grid_points_x)
                - get_height(bm, x + 1, y, grid_points_x)
            ) * u

            # calculate new direction from old direction and gradient
            d_dir_new_x = d_dir_old_x * p_inertia - g_d_pos_old_x * (1 - p_inertia)
            d_dir_new_y = d_dir_old_y * p_inertia - g_d_pos_old_y * (1 - p_inertia)

            # if the new direction is 0,0 then give it a random direction
            if d_dir_new_x == 0.0 and d_dir_new_y == 0.0:
                random_angle = random.uniform(0.0, 2.0 * math.pi)
                d_dir_new_x = math.cos(random_angle)
                d_dir_new_y = math.sin(random_angle)

            # normalize the new direction
            d_dir_new_len = math.sqrt(
                d_dir_new_x * d_dir_new_x + d_dir_new_y * d_dir_new_y
            )
            d_dir_new_x /= d_dir_new_len
            d_dir_new_y /= d_dir_new_len

            # calculate new position
            d_pos_new_x = d_pos_old_x + d_dir_new_x
            d_pos_new_y = d_pos_old_y + d_dir_new_y

            # if the new position is off the grid then dont do anything???
            if (
                d_pos_new_x < 0.0
                or d_pos_new_x > float(grid_len_x)
                or d_pos_new_y < 0.0
                or d_pos_new_y > float(grid_len_y)
            ):
                break

            # calculate the height difference between new and old position
            h_dif = get_height_interpolate(
                bm, d_pos_new_x, d_pos_new_y, grid_points_x
            ) - get_height_interpolate(bm, d_pos_old_x, d_pos_old_y, grid_points_x)

            # calculate the capacity of this droplet
            d_cap = max(-h_dif, p_minslope) * d_vel * d_water * p_capacity

            # if drop has more sediment than capacity, drop a percentage (p_deposition) at p_old
            if d_sediment > d_cap:
                sediment_to_deposit = (d_sediment - d_cap) * p_deposition
                d_sediment -= sediment_to_deposit
                give_sediment(
                    bm,
                    grid_points_x,
                    sediment_to_deposit,
                    d_pos_old_x,
                    d_pos_old_y,
                )
            # if drop has less sediment than capacity, take a percentage of remaining capacity (p_erosion) of p_old.
            else:
                sediment_to_take = min((d_cap - d_sediment) * p_erosion, -h_dif)
                d_sediment += sediment_to_take
                take_sediment(
                    bm,
                    grid_points_x,
                    grid_points_y,
                    p_radius,
                    sediment_to_take,
                    d_pos_old_x,
                    d_pos_old_y,
                )

            # adjust vel - the max is sus since it should never be negative!!!!!!!!
            d_vel = math.sqrt(max(0.0, d_vel * d_vel - h_dif * p_gravity))

            # evaporate water
            d_water = d_water * (1.0 - p_evaporation)

            # we no longer need the d_pos_old so the old becomes the new
            d_pos_old_x = d_pos_new_x
            d_pos_old_y = d_pos_new_y
