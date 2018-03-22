#coding: utf-8

import datajoint as dj
dj.config['display.show_tuple_count'] = False

schema = dj.schema('alyssa_microns_ta3', locals()) 
nda    = dj.create_virtual_module('nda', 'microns_nda')

# Do we want to include the timestamp on all the classification-type tables below? If so, then we need to be careful about selecting
# only the most recent entry for each segment when querying these tables for other computations.


# Tables defining the segmentation and segments
# ----------------------------------------------------------------------

@schema
class Segmentation(dj.Manual):
    definition = """
    # Segmentation iteration or snapshot
    segmentation : smallint  # segmentation id
    ---
    segmentation_description = "" : varchar(4000)  # free text description of the segmentation
    """

# Need to define a standard for the key point location (possibly different for different types of objects)
@schema
class Segment(dj.Manual):
    definition = """
    # Segment: a volumetric segmented object
    -> Segmentation
    segment_id : bigint  # segment id that is unique within each Segmentation
    ---
    vset_id = null     : bigint unsigned     # Place in storage (if applicable)
    key_point_x        : int                 # (um)
    key_point_y        : int                 # (um)
    key_point_z        : int                 # (um)
    x_min              : int                 # (um) bounding box
    y_min              : int                 # (um) bounding box
    z_min              : int                 # (um) bounding box
    x_max              : int                 # (um) bounding box
    y_max              : int                 # (um) bounding box
    z_max              : int                 # (um) bounding box
    """


# Tables defining proofreaders and proofreading changes
# ----------------------------------------------------------------------

# Need to define a method to add a new proofreader
@schema
class Proofreader(dj.Lookup):
    definition = """
    # EM Segmentation proofreaders
    proofreader : varchar(8)  # short name (initials)
    """
    contents = zip(('Alyssa','Nick','Tommy')) # Change to initials?

@schema
class Proofread(dj.Manual):
    definition = """
    # list of proofreading actions performed on a Segmentation
    -> Segment
    proofread_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    verdict : enum('valid','deprecated','ambiguous')
    proofread_comment = "" : varchar(4000)
    """
    

# Tables defining classifications of segments at multiple levels
# ----------------------------------------------------------------------

# Fix the list of designations to make sure it is mostly inclusive and options are
# mutually exclusive

# Why do the definition of the primary key as below and not as an enum type, for instance?
# Check the DataJoint tutorial to see if you can figure out the answer.
@schema
class SegmentDesignationLookup(dj.Lookup):
    definition = """
    # list of possible general designations for an object
    designation : varchar(255)
    """
    contents = zip(('neuron','glia','astrocyte','vessel','ambiguous'))

@schema
class SegmentDesignation(dj.Manual):
    definition = """
    # classification of segments into general tissue feature types
    -> Segment
    designation_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> SegmentDesignationLookup
    designation_comment = "" : varchar(4000)
    """
    

@schema
class NeuronTypeLookup(dj.Lookup):
    definition = """
    # list of possible known neuron types
    neuron_type : varchar(255)
    """
    contents = zip(('small_basket','large_basket','Martinotti','bipolar','neurogliaform','chandelier','pyramidal','ambiguous'))

@schema
class NeuronType(dj.Manual):
    definition = """
    # classification of neuronal segments into known types
    -> Segment
    neuron_type_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> NeuronTypeLookup
    neuron_type_comment = "" : varchar(4000)
    """
    

@schema
class DendriteTypeLookup(dj.Lookup):
    definition = """
    # possible types of dendrites for neuronal segments
    dendrite_type : varchar(255)
    """
    contents = zip(('spiny','sparsely_spiny','aspiny','ambiguous'))

@schema
class DendriteType(dj.Manual):
    definition = """
    # classification of neuronal segments according to appearance of dendritic spines
    -> Segment
    dendrite_type_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> DendriteTypeLookup
    dendrite_type_comment = "" : varchar(4000)
    """
    
    
@schema
class NeuriteTypeLookup(dj.Lookup):
    definition = """
    # list of possible types of neurites
    neurite_type : varchar(255)
    """
    contents = zip(('axon','dendrite','ambiguous'))

@schema
class NeuriteType(dj.Manual):
    definition = """
    # classification of neurites (not attached to a cell body) into axon or dendrite if possible
    -> Segment
    neurite_type_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> NeuriteTypeLookup
    neurite_type_comment = "" : varchar(4000)
    """
    

# Tables defining classifications of neuronal segments
# ----------------------------------------------------------------------

# We may want to restrict the segment_ids for each entry in each of these
# tables to be one that has the neuron segment designation to enforce 
# consistency.
# Do we need to run checks regularly on the table values?
# Probably a good idea. Also should update table values whenever a split
# or merge error is corrected.
# Do we want such methods to be run automatically when someone makes a
# change in Neuroglancer, or whenever a change is made to the chunked
# graph, for instance?
# This table has to be populated manually, correct? (Because the segment_ids need
# to be specified and then values for those segments need to be pulled
# from other tables?)

# YOU NEED TO DROP AND RE-DEFINE THESE TABLES ONCE YOU GET THE NDA PART WORKING
@schema
class NeuronSoma(dj.Manual): # Do you need to change this table type to computed? Look at the DataJoint documentation again
    definition = """
    # table of neuronal segments that have soma contained in the volume
    -> Segment
    neuron_soma_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> DendriteType
    -> NeuronType
    neuron_soma_comment = "" : varchar(4000)
    """
    # To add back in later: -> nda.EMcell
    
    
# Look at the nda schema and figure out what the nda.mask table is
@schema
class Neurite(dj.Manual):
    definition = """
    # table of neuronal segments without a soma contained in the volume
    -> Segment
    neurite_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> DendriteType
    -> NeuriteType
    neurite_comment = "" : varchar(4000)
    """
    # To add back in later: -> nda.mask
    


# Tables containing graphical representations of segments
# ----------------------------------------------------------------------

@schema
class SegmentMesh(dj.Manual):
    definition = """
    # Trimesh of Segment
    -> Segment
    """
    
    # Will there really be few enough fragments that smallint is a large enough type?
    class Fragment(dj.Part):
        definition = """
        # SegmentMesh Fragment
        -> SegmentMesh
        fragment    : smallint    # fragment in mesh
        ---
        bound_x_min : int         # (um) bounding box
        bound_y_min : int         # (um) bounding box
        bound_z_min : int         # (um) bounding box
        bound_x_max : int         # (um) bounding box
        bound_y_max : int         # (um) bounding box
        bound_z_max : int         # (um) bounding box
        n_vertices  : int         # number of vertices in this mesh
        n_triangles : int         # number of triangles in this mesh
        vertices    : longblob    # x,y,z coordinates of vertices
        triangles   : longblob    # triangles (triplets of vertices)
        """

@schema
class SegmentVoxelList(dj.Manual):
    definition = """
    # list of voxels occupied by Segment
    -> Segment
    ---
    voxels : longblob    # x,y,z coordinates of voxels
    """

# Do you want to expand this dictionary out into explicit properties of the skeleton?
# Or is it better instead to point to a different place that contains the skeletons? Probably this method is less robust
# because it is less contained.
@schema
class SegmentSkeleton(dj.Manual):
    definition = """
    # skeleton of Segment
    -> Segment
    ---
    skeleton : longblob    # dictionary containing nodes, edges, and node labels of skeleton
    """


# Tables defining synapses between neuronal segments
# ----------------------------------------------------------------------
   
@schema
class Synapse(dj.Manual):
    definition = """
    # anatomically localized synapse between two Segments
    -> Segmentation
    synapse_id : bigint # synapse index within the segmentation
    ---
    (presyn)  -> Segment
    (postsyn) -> Segment
    synapse_x             : float
    synapse_y             : float
    synapse_z             : float
    """

@schema
class SynapseProofread(dj.Manual):
    definition = """
    # proofreading actions performed on synapses
    -> Synapse
    proofread_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    verdict : enum('valid','deprecated','ambiguous')
    proofread_comment = "" : varchar(4000)
    """
    

@schema
class SynapseTypeLookup(dj.Lookup):
    definition = """
    # list of possible synapse types
    synapse_type : varchar(255)
    """
    contents = zip(('asymmetric','symmetric','ambiguous'))

@schema
class SynapseType(dj.Manual):
    definition = """
    # classification of synapses into types
    -> Synapse
    synapse_type_timestamp = CURRENT_TIMESTAMP : timestamp
    ---
    -> Proofreader
    -> SynapseTypeLookup
    synapse_type_comment = "" : varchar(4000)
    """
    

# Possibly add a table that links synapses to meshes of their PSDs
# (this is a feature that people are working on nets to detect)


# Tables defining ultrastructure for Segments
# ----------------------------------------------------------------------

# Table for mitochondria?



# Change log
# ----------------------------------------------------------------------





























