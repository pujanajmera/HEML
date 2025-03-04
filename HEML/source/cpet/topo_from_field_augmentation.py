from posixpath import split
from tkinter import E
import os, re, json
from glob import glob
from HEML.utils.data import (
    get_options,
    check_if_file_is_empty,
    get_fe_positions,
    get_ligand_info,
    get_N_positions,
    check_if_dict_has_None,
)


def write_topo(
    outdir_cpet, file_name, samples, bins, step_size, box_size, arg1, arg2, arg3, uuid=1
):
    options = open(f"{outdir_cpet}options_topology_{file_name}_{uuid}.txt", "w+")
    options.write(
        f'align {arg1[0]}:{arg1[1]}:{arg1[2]} {nitrogen_dict["N1_xyz"][0]}:{nitrogen_dict["N1_xyz"][1]}:{nitrogen_dict["N1_xyz"][2]} {nitrogen_dict["N2_xyz"][0]}:{nitrogen_dict["N2_xyz"][1]}:{nitrogen_dict["N2_xyz"][2]}\n'
    )
    options.write(f"%topology \n")
    options.write("    volume box {} {} {} \n".format(box_size, box_size, box_size))
    options.write("    stepSize {} \n".format(step_size))
    options.write("    samples {} \n".format(samples))
    options.write("    sampleOutput {} \n".format(file_name))
    options.write("    bins {} \n".format(bins))
    options.write(f"end \n")
    options.close()


if __name__ == "__main__":
    zero_active = True
    zero_everything_charged = False

    box = False
    box_size = 3.0

    fail = 0
    options = get_options("./options_aug.json")

    outdir = options["processed_charges_folder"]
    outdir_cpet = options["cpet_folder"]
    charges_directory = options["charges_folder"]

    filelist = glob(charges_directory + "*pqr")

    for i in filelist:
        # new filename
        filename = os.path.basename(i)
        listname = filename.split(".")

        # check that output isn't already there in the processed directory
        output = f"{outdir}{listname[0]}.pqr"
        if os.path.exists(output):
            print("output file already exists")

        # checks that input file is not empty
        if check_if_file_is_empty(i):
            print("input file is empty")
            pass

        else:
            openfile = open(i)
            readfile = openfile.readlines()
            openfile.close
            filename = i.split(".")[0]

            # Look for FE in each line, and get chain:res:atom ID and xyz coords if exists.

            fail_cond = True

            ligand_dict = {}
            nitrogen_dict = {}

            try:
                fe_dict = get_fe_positions(i)
                assert fe_dict["id"] != None
                print(fe_dict["id"], fe_dict["xyz"])
                ligand_dict = get_ligand_info(i, fe_dict["xyz"])
                nitrogen_dict = get_N_positions(i, fe_dict["id"], fe_dict["xyz"])
                nitro_none = check_if_dict_has_None(nitrogen_dict)
                ligand_none = check_if_dict_has_None(ligand_dict)
                if not nitro_none and not ligand_none:
                    fail_cond = False

                    if ligand_dict["best_crit_dist"] > 4.0:
                        print(ligand_dict["best_crit_dist"])
                        print(
                            f"ERROR: No cysteine/tyrosine/histine ligand found for {i}.\n"
                        )
                        fail += 1
                        continue

                    else:
                        print(f'Nitro 1 {nitrogen_dict["N_ID1"]}')
                        print(f'Nitro 2 {nitrogen_dict["N_ID2"]}')
                        print(f'Nitro 3 {nitrogen_dict["N_ID3"]}')
                        print(f'Nitro 4 {nitrogen_dict["N_ID4"]}')
                        print(f'ligand of note {ligand_dict["best_crit"]}\n')

            except:
                fail_cond = True
                print("Failed File: ".format(i))
                fail += 1

            filename = os.path.basename(i)
            listname = filename.split(".")

            if not fail_cond:
                ligand_identifier = ligand_dict["best_crit"].split(":")

                with open(output, "w") as outfile:
                    for j in readfile:
                        line_split = re.split(r"(\s+)", j)
                        cond = (
                            line_split[8] == ligand_identifier[0]
                            and line_split[10] == ligand_identifier[1]
                        )

                        if zero_active and ("HETATM" in line_split[0] or cond):
                            temp_write = j[:56] + "0.000" + j[61:]
                            outfile.write(temp_write)
                        elif zero_everything_charged and line_split[3] in [
                            "ASP",
                            "GLU",
                            "LYS",
                            "ARG",
                            "HIS",
                        ]:
                            temp_write = j[:56] + "0.000" + j[61:]
                            outfile.write(temp_write)
                        else:
                            outfile.write(j)

                file_name = i.split("/")[-1].split(".")[0]

                samples = 1000
                bins = 20
                step_size = 0.001
                arg1 = nitrogen_dict["mean_N_xyz"]
                arg2 = nitrogen_dict["N1_xyz"]
                arg3 = nitrogen_dict["N2_xyz"]
                arg4 = ligand_dict["crit_xyz"]
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg2,
                    arg3,
                    uuid=1,
                )
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg3,
                    arg2,
                    uuid=2,
                )
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg2,
                    arg4,
                    uuid=3,
                )
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg4,
                    arg2,
                    uuid=6,
                )
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg3,
                    arg4,
                    uuid=4,
                )
                write_topo(
                    outdir_cpet,
                    file_name,
                    samples,
                    bins,
                    step_size,
                    box_size,
                    arg1,
                    arg4,
                    arg3,
                    uuid=5,
                )

    print("fail count: {}".format(fail))
