'''
This file automates the virtual evaluation of Vladislav Klass' master thesis.
'''
import matplotlib.pyplot as plt
import pandas as pd
from numpy import NaN
from pyDOE import *

from fmp_synthetic_data_preprocessing import findAllFile, findAllSubdirectories
from fmp_thesis_evaluation_policy_klass import run_dex_net


def run_virtual_experiments(model_name, camera_intr_filename, config_filename, evaluation_dir):

    ''' 
    setup design of experiment (DOE) schedule.

    Parameters that are varied and their range: 
    1. part [all part subfolders within './data/virtual_evaluation']
    2. user input point [all points in '/user_input_points/' subdirectory]

    3. user_input_fusion_method ["masking", "linear_distance_scaling", "quadratic_distance_scaling"]
    4. user_input_weight ["zero", "very low", "low", "medium", "high", "very high"]
    '''

    # find all object directories
    object_list = sorted(findAllSubdirectories(evaluation_dir))

    # setup up evaluation scheme

    evaluation_template = {'object_path':[], 
                            'user_input_point_number':[], 
                            'user input fusion method':[], 
                            'user input weight':[], 
                            'distance_grasp_to_user_input_norm':[], 
                            'grasp_quality':[], 
                            'mean_evaluation_metric':[]}

    evaluation_scheme = pd.DataFrame(data=evaluation_template)

    for _, object_dir in enumerate(object_list):
        # get all camera view points
        print("Load object:" + object_dir)
        view_list = sorted(findAllFile(object_dir, 'depth_raw.png'))
        for view_idx, view in enumerate(view_list[0:1]): # to save computatin time, only use the first view
            # set paths
            camera_pose_path = object_dir + "/poses/" + str(view_idx) + "_pose.txt"
            user_input_3d_folder = object_dir + "/user_input_points"

            point_list = sorted(findAllFile(object_dir + "/user_input_points/", 'point.txt'))
            # iterate through all saved user input points 
                
            if "suction" in config_filename or "dex-net_3.0" in config_filename:
                # load segmentation mask

                last_slash_index = object_dir[::-1].index("/")
                obect_name = object_dir[-last_slash_index:]

                segmask_filename = evaluation_dir + "/../masks/" + obect_name + "_mask/" + str(view_idx) + ".png"
            else: 
                segmask_filename = None

            for user_input_fusion_method in ["masking", "linear_distance_scaling", "quadratic_distance_scaling"]: # ["masking", "linear_distance_scaling", "quadratic_distance_scaling"]:
                for user_input_weight in ["low", "medium", "high", "very high"]: # ["low", "medium", "high", "very high"]
                    for point_idx in range(min(len(point_list), 10)): # limit user input points max to save computation time

                        try:
                            mean_evaluation_metric, grasp_quality, distance_grasp_to_user_input_norm = run_dex_net(
                                model_name,
                                depth_ims_dir  = None,
                                depth_im_filename = view, 
                                segmask_filename = segmask_filename, 
                                camera_intr_filename = camera_intr_filename, 
                                model_dir = None, 
                                config_filename = config_filename, 
                                fully_conv = None, 
                                camera_pose_path = camera_pose_path, 
                                user_input_3d_folder = user_input_3d_folder, 
                                user_input_fusion_method = user_input_fusion_method, 
                                user_input_weight = user_input_weight,
                                user_input_point_number = point_idx
                                )
                            print(mean_evaluation_metric, grasp_quality, distance_grasp_to_user_input_norm)
                            experiment = pd.DataFrame({'object_path': [object_dir], 
                            'user_input_point_number':[point_idx], 
                            'user input fusion method':[user_input_fusion_method], 
                            'user input weight':[user_input_weight], 
                            'distance_grasp_to_user_input_norm':[distance_grasp_to_user_input_norm], 
                            'grasp_quality':[grasp_quality], 
                            'mean_evaluation_metric':[mean_evaluation_metric]})
                        except:
                            # If no valid grasps are found
                            print("No valid grasp")
                            experiment = pd.DataFrame({'object_path': [object_dir], 
                            'user_input_point_number':[point_idx], 
                            'user input fusion method':[user_input_fusion_method], 
                            'user input weight':[user_input_weight], 
                            'distance_grasp_to_user_input_norm':[NaN], 
                            'grasp_quality':[0], 
                            'mean_evaluation_metric':[0]})
                        
                        evaluation_scheme = evaluation_scheme.append(experiment)

    
        # Save data to csv
        evaluation_scheme.to_csv(evaluation_dir + '/virtual_experiments_results_suction.csv', index=False)        

def postprocess_experiment_data(evaluation_file_path):
    # df = pd.read_csv(evaluation_dir + '/virtual_experiments_results.csv')
    data = pd.read_csv(evaluation_file_path)
    data['user input weight'] = pd.Categorical(data['user input weight'], ["low", "medium", "high", "very high"])

    masking_data = data[data["user input fusion method"] == "masking"]
    linear_distance_scaling_data = data[data["user input fusion method"] == "linear_distance_scaling"]
    quadratic_distance_scaling_data = data[data["user input fusion method"] == "quadratic_distance_scaling"]
    
    fig, axs = plt.subplots(3)
    fig.set_size_inches(5.8, 7.6)

    plot_data = {"data": [masking_data, linear_distance_scaling_data, quadratic_distance_scaling_data], "names": ["masking", "linear distance scaling", "quadratic distance scaling"]}
    for ax_idx, ax in enumerate(axs): # range(len(plot_data["data"])): # [masking_data, linear_distance_scaling_data, quadratic_distance_scaling_data]:
        # if ax_idx==0:     
        #     
        means = plot_data["data"][ax_idx].groupby(["user input weight"]).mean()
        means = means.drop(["user_input_point_number"], axis=1)
        means.plot.bar(ax=ax, color=['#0065BD', '#64A0C8', '#98C6EA'])
        ax.get_legend().remove()
        title = chr(97 + ax_idx) + ")"
        ax.set_title(title, loc='left')
        ax.set_ylim([0, 1])
        if ax_idx < 2:
            ax.set_xlabel("")
            x_labels = ax.get_xticklabels()
            ax.set_xticklabels(x_labels, rotation=0)

    plt.legend(["mean distance metric", "mean grasp quality", "mean evaluation metric"] ) 

    plt.xticks(rotation='horizontal')
    plt.show()
    fig.savefig('Results_pj.png', dpi=100)



    # One figure only
    # plot_data = {"data": [masking_data, linear_distance_scaling_data, quadratic_distance_scaling_data], "names": ["masking", "linear distance scaling", "quadratic distance scaling"]}
    # for i in range(len(plot_data["data"])): # [masking_data, linear_distance_scaling_data, quadratic_distance_scaling_data]:
    #     means = plot_data["data"][i].groupby(["user input weight"]).mean()
    #     means = means.drop(["user_input_point_number"], axis=1)
    #     means.plot.bar(color=['#0065BD', '#64A0C8', '#98C6EA'])
    #     plt.title("Virtual evaluation result for  " + plot_data["names"][i] + " method")
    #     plt.legend(["mean distance metric", "mean grasp quality", "mean evaluation metric"], loc="lower center", bbox_to_anchor=(0.5,-0.27)) 
    #     plt.xlabel("User input weight")
    #     fig = plt.gcf()
    #     fig.set_size_inches(5.8, 5)
    #     fig.savefig('test2png.png', dpi=100)
    #     plt.tight_layout()
    #     plt.show()

        
if __name__ == '__main__':
    
    model_name = "GQCNN-4.0-SUCTION" #  GQCNN-4.0-PJ GQCNN-2.0 GQCNN-4.0-SUCTION GQCNN-3.0 FCGQCNN-4.0-SUCTION
    camera_intr_filename = "data/calib/basler/basler.intr"
    config_filename = "cfg/examples/replication/dex-net_4.0_suction.yaml" # dex-net_4.0_pj.yaml dex-net_2.0.yaml dex-net_4.0_suction.yaml
    evaluation_dir = "/home/vladislav/gqcnn/data/virtual_evaluation/19objs4vladi/renderings/"

    # run_virtual_experiments(model_name, camera_intr_filename, config_filename, evaluation_dir)


    file_name = "virtual_experiments_results_pj.csv"
    evaluation_file_path = evaluation_dir + file_name
    postprocess_experiment_data(evaluation_file_path)



