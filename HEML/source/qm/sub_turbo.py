import warnings, os, argparse

warnings.filterwarnings("ignore", category=DeprecationWarning)


from HEML.utils.data import create_folders, get_options, put_charges_in_turbo_files
from HEML.utils.turbomole import (
    define_turbomoleio,
    get_frozen_atoms,
    get_elements,
    add_frozen_atoms,
    check_submitted,
    clean_up,
    fetch_charges_dict,
    submit_turbomole,
    write_memory_header_to_control,
)


def main():
    submit_tf = False
    submit_only = True
    cleanup_tf = False
    embedd_tf = False
    clear_control_tf = False

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--options", help="location of options file", default="./options/options.json"
    )
    options_loc = parser.parse_args().options
    options = get_options(options_loc)

    root = options["compressed_proteins_folder"]
    x2t_loc = options["x2t_loc"]

    for ind, protein_name in enumerate(os.listdir(root)):
        if os.path.isdir(os.path.join(root, protein_name)):
            print(protein_name)

            folder_name = root + protein_name

            if cleanup_tf:
                clean_up(
                    "{}/embedding/o/".format(folder_name),
                    filter=None,
                    clear_control_tf=clear_control_tf,
                )
                clean_up(
                    "{}/embedding/oh/".format(folder_name),
                    filter=None,
                    clear_control_tf=clear_control_tf,
                )
                clean_up(
                    "{}/embedding/normal/".format(folder_name),
                    filter=None,
                    clear_control_tf=clear_control_tf,
                )

            if submit_only:
                submit_turbomole(
                    "{}/embedding/o/".format(folder_name),
                    t=24,
                    n=6,
                    job_name="{}_o".format(protein_name),
                )
                submit_turbomole(
                    "{}/embedding/oh/".format(folder_name),
                    t=24,
                    n=6,
                    job_name="{}_oh".format(protein_name),
                )
                submit_turbomole(
                    "{}/embedding/normal/".format(folder_name),
                    t=24,
                    n=6,
                    job_name="{}_normal".format(protein_name),
                )
                # go to next protein
                continue

            create_folders(folder_name)

            if not check_submitted(folder_name):
                try:
                    os.system(
                        "{} {}/{}_heme_h.xyz > {}/embedding/normal/coord".format(
                            x2t_loc, folder_name, protein_name, folder_name
                        )
                    )
                    os.system(
                        "{} {}/{}_o_heme_h.xyz > {}/embedding/o/coord".format(
                            x2t_loc, folder_name, protein_name, folder_name
                        )
                    )
                    os.system(
                        "{} {}/{}_oh_heme_h.xyz > {}/embedding/oh/coord".format(
                            x2t_loc, folder_name, protein_name, folder_name
                        )
                    )

                    # get some info from xyz
                    frozen_atoms_oh = get_frozen_atoms(
                        "{}/{}_oh_heme_h.xyz".format(folder_name, protein_name)
                    )
                    frozen_atoms_o = get_frozen_atoms(
                        "{}/{}_o_heme_h.xyz".format(folder_name, protein_name)
                    )
                    frozen_atoms_heme = get_frozen_atoms(
                        "{}/{}_heme_h.xyz".format(folder_name, protein_name)
                    )

                    elements = get_elements(
                        "{}/{}_heme_h.xyz".format(folder_name, protein_name)
                    )
                    # add frozen atoms to coord files
                    add_frozen_atoms(
                        "{}/embedding/oh/".format(folder_name), frozen_atoms_oh
                    )
                    add_frozen_atoms(
                        "{}/embedding/o/".format(folder_name), frozen_atoms_o
                    )
                    add_frozen_atoms(
                        "{}/embedding/normal/".format(folder_name), frozen_atoms_heme
                    )

                    try:
                        define_turbomoleio(
                            "{}/embedding/normal/".format(folder_name),
                            frozen_atoms_heme,
                            elements,
                            charge=-2,
                            spin=1,
                            new_control=clear_control_tf,
                        )
                        write_memory_header_to_control(
                            "{}/embedding/normal/".format(folder_name), 1800
                        )
                    except:
                        print("failed to define turbomoleio for normal")

                    try:
                        define_turbomoleio(
                            "{}/embedding/oh/".format(folder_name),
                            frozen_atoms_oh,
                            elements,
                            charge=-2,
                            spin=0,
                            new_control=clear_control_tf,
                        )
                        write_memory_header_to_control(
                            "{}/embedding/oh/".format(folder_name), 1800
                        )
                    except:
                        print("failed to define turbomoleio for oh")
                        # add to log

                    try:
                        define_turbomoleio(
                            "{}/embedding/o/".format(folder_name),
                            frozen_atoms_o,
                            elements,
                            charge=-3,
                            spin=0,
                            new_control=clear_control_tf,
                        )
                        write_memory_header_to_control(
                            "{}/embedding/o/".format(folder_name), 1800
                        )
                    except:
                        print("failed to define turbomoleio for o")

                    if embedd_tf:
                        # find pqr file in fsqueueuolder
                        pqr_file = [
                            f for f in os.listdir(folder_name) if f.endswith(".pqr")
                        ][0]
                        charges_dict = fetch_charges_dict(
                            os.path.join(folder_name, pqr_file), convert_to_bohr=True
                        )
                        # print("-"*20 + "charges fetched" + "-"*20)

                        put_charges_in_turbo_files(
                            os.path.join(folder_name, "/embedding/oh/"), charges_dict
                        )
                        put_charges_in_turbo_files(
                            os.path.join(folder_name, "/embedding/o/"), charges_dict
                        )
                        put_charges_in_turbo_files(
                            os.path.join(folder_name, "/embedding/normal/"),
                            charges_dict,
                        )

                    if submit_tf:
                        submit_turbomole(
                            "{}/embedding/o/".format(folder_name),
                            t=24,
                            n=6,
                            job_name="{}_o".format(protein_name),
                        )
                        submit_turbomole(
                            "{}/embedding/oh/".format(folder_name),
                            t=24,
                            n=6,
                            job_name="{}_oh".format(protein_name),
                        )
                        submit_turbomole(
                            "{}/embedding/normal/".format(folder_name),
                            t=24,
                            n=6,
                            job_name="{}_normal".format(protein_name),
                        )

                    else:
                        print("not submitting calculations")

                    print("done with {} of {}".format(ind, len(os.listdir(root))))

                except:
                    print("-----> error with {}".format(protein_name))
                    continue


main()
