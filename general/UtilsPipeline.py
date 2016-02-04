__author__ = 'lenk'

import argparse
import sys
import subprocess
import os
import shutil
import multiprocessing
import datetime

import quast

import rqconfig

import UtilsGeneral


def get_arguments():
    # use --help for running without arguments:
    if len(sys.argv) == 1:
        command = 'python {} -h'.format(sys.argv[0])
        subprocess.call(command, shell=True)
        sys.exit(0)

    version, build = UtilsGeneral.get_version(rqconfig.GENERAL_LOCATION)

    parser = \
        argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                description="QUALITY ASSESSMENT FOR TRANSCRIPTOME ASSEMBLIES %(prog)s v.{}"
                                              "\n\nUsage:\npython %(prog)s --transcripts TRANSCRIPTS --reference REFERENCE --gene_database GENE_DATABASE".format(version),
                                              #"    pipeline-2: python %(prog)s -p2 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION
                                              #"    pipeline-1: python %(prog)s -p1 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --alignment ALIGNMENT\n"
                                              #"    pipeline-2: python %(prog)s -p2 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION\n"
                                              #"    pipeline-3: python %(prog)s -p3 --reference REFERENCE --annotation ANNOTATION --assembler ASSEMBLER --left_reads LEFT_READS --right_reads RIGHT_READS\n"
                                              #"    pipeline-4: python %(prog)s -p4 --reference REFERENCE --annotation ANNOTATION --simulator SIMULATOR --par PAR --assembler ASSEMBLER\n",
                                #epilog='If you don\'t use prepared arguments, please add to PATH samtools, bowtie or bowtie-build for fusion and misassamble analyze.', conflict_handler='resolve', prog=sys.argv[0])
                                epilog='Don\'t forget to add GMAP (or BLAT) to PATH.', conflict_handler='resolve', prog=sys.argv[0])


    # PIPELINES:
    #groupPipelines = parser.add_argument_group('Pipeline options')

    #groupChoosePipelines = groupPipelines.add_mutually_exclusive_group(required=False)
    #groupChoosePipelines.add_argument("-p1", "--use_alignment_annotation", action="store_true", help='Use this pipeline-1 if you have FASTA-file with assembled transcripts, database with reference, GTF or GFF-file with annotation, PSL-file with alignment')
    #groupChoosePipelines.add_argument("-p2", "--use_reference_transcripts_annotation", action="store_true", help='Use this pipeline-2 if you have FASTA-file with assembled transcripts, database with reference and GTF or GFF-file with annotation')
    #groupChoosePipelines.add_argument("-p3", "--use_reference_reads_annotation", action="store_true", help='Use this pipeline-3 if you have database with reference, GTF or GFF-file with annotation and FASTQ-file with reads')
    #groupChoosePipelines.add_argument("-p4", "--use_reference_annotation", action="store_true", help='Use this pipeline-4 if you have database with reference and GTF or GFF-file with annotation')

    # INPUT DATA:
    group_input_data = parser.add_argument_group('Input data')
    group_input_data.add_argument('-r', '--reference',
                                  help='Single file with reference genome in FASTA format OR *.txt file with '
                                       'one-per-line list of FASTA files with reference sequences', type=str)

    group_input_data.add_argument('-gtf', '--gene_database',
                                  help='File with gene database. We recommend to use files downloaded from GENCODE '
                                       'or Ensembl [GTF/GFF]', type=str)
    #group_input_data.add_argument('-g', '--genes', help='File with gene coordinates in the reference for prokaryotes [GFF]', type=str)
    #group_input_data.add_argument('-o', '--operons', help='File with operon coordinates in the reference for prokaryotes [GFF]', type=str)

    group_input_data.add_argument('-c', '--transcripts', help='File(s) with transcripts [FASTA]', type=str, nargs='+')

    group_input_data.add_argument('-psl', '--alignment', help='File(s) with transcripts alignments to the reference genome [PSL]', type=str, nargs='+')

    group_input_data.add_argument('-sam', '--reads_alignment', help='File with reads alignments to the reference genome [SAM]')

    group_input_data.add_argument('-1', '--left_reads', help='File with forward paired-end reads [FASTQ]', type=str)
    group_input_data.add_argument('-2', '--right_reads', help='File with reverse paired-end reads [FASTQ]', type=str)
    # group_input_data.add_argument('-12', '--paired_reads', help='File with interplaced forward and reverse paired-end reads [FASTQ]')
    group_input_data.add_argument('-s', '--single_reads', help='File with unpaired reads [FASTQ]', type=str)

    #group_input_data.add_argument('--par', help='File with simulation parameters, for details go to http://sammeth.net/confluence/'
    #                                    'display/SIM/.PAR+Simulation+Parameters [PAR]', type=str)

    # BASIC OPTIONS:
    group_basic = parser.add_argument_group('Basic options')
    group_basic.add_argument('-o', '--output_dir', help='Directory to store all results [default: rnaQUAST_results/results_<datetime>]', type=str)
    group_basic.add_argument('--test', help='Run rnaQUAST on the test data from the test_data folder, output directory is rnaOUAST_test_output', action='store_true')
    group_basic.add_argument('-d', '--debug', help='Report detailed information, typically used only for detecting problems.', action='store_true')

    group_advanced = parser.add_argument_group('Advanced options')
    group_advanced.add_argument('-t',  '--threads', help='Maximum number of threads, default: min(number of CPUs / 2, 16)', type=int)

    group_advanced.add_argument('-l', '--labels', help='Name(s) of assemblies that will be used in the reports', type=str, nargs='+')

    group_advanced.add_argument('-ss', '--strand_specific', help='Set if transcripts were assembled using strand-specific RNA-Seq data', action='store_true')

    group_advanced.add_argument('--min_alignment', help='Minimal alignment length, default: %(default)s', type=int, default=50, required=False)

    group_advanced.add_argument('--no_plots', help='Do not draw plots (to speed up computation)', action='store_true')

    group_advanced.add_argument('--blat', help='Run with BLAT alignment tool (http://hgwdev.cse.ucsc.edu/~kent/exe/) instead of GMAP', action='store_true')

    group_advanced.add_argument('--busco', help='Run with BUSCO tool (http://busco.ezlab.org/)', action='store_true')
    # group_advanced.add_argument('-C', '--cegma', help='Run with CEGMA (Core Eukaryotic Genes Mapping Approach)', action='store_true')

    group_advanced.add_argument('--tophat', help='Run with TopHat tool (https://ccb.jhu.edu/software/tophat/index.shtml) instead of STAR', action='store_true')

    group_advanced.add_argument('--gene_mark', help='Run with GeneMarkS-T tool (http://topaz.gatech.edu/GeneMark/)', action='store_true')
    # groupSpecies = group_basic.add_mutually_exclusive_group(required=False)
    # groupSpecies.add_argument('--eukaryote', help='Genome is eukaryotic', action='store_true')

    group_advanced.add_argument('--lower_threshold', help='Lower threshold for x-assembled/covered/matched metrics, default: %(default)s', type=float, default=0.5, required=False)
    group_advanced.add_argument('--upper_threshold', help='Upper threshold for x-assembled/covered/matched metrics, default: %(default)s', type=float, default=0.95, required=False)

    # group_advanced.add_argument('-ir', '--isoforms_range', help='Range of isoforms lengths involved in metrics', type=int, nargs='+')
    #group_advanced.add_argument('-fma', '--fusion_misassemble_analyze', help='Analyze fusions and misassemblies', action='store_true')


    group_gffutils = parser.add_argument_group('Gffutils related options')
    group_gffutils.add_argument('--disable_infer_genes', help='Use this option if your GTF file already contains genes records', action='store_true')
    group_gffutils.add_argument('--disable_infer_transcripts', help='Use this option if your GTF already contains transcripts records', action='store_true')
    group_gffutils.add_argument('--store_db', help='Save new complete gene database generated by gffutils (speeds up next runs with these database)', action='store_true')


    group_busco = parser.add_argument_group('BUSCO related options')
    group_busco.add_argument('--clade', help='Path to the BUSCO lineage data to be used (Eukaryota, Metazoa, Arthropoda, Vertebrata or Fungi)', type=str)

    group_gene_mark = parser.add_argument_group('GeneMarkS-T related options')
    group_gene_mark.add_argument('--prokaryote', help='Use this option if the genome is prokaryotic', action='store_true')

    # TOOLS:
    #groupTools = parser.add_argument_group('Tools')
    #groupTools.add_argument('--assembler', help='Choose assembler to get FASTA-file with transcripts', type=str, choices=['Trinity', 'SPAdes'], nargs='+')
    #groupTools.add_argument('--simulator', help='Choose simulator to get FASTQ-file with reads', type=str, choices=['Flux'])

    args = parser.parse_args()

    return args


#pipeline-1: python %(prog)s -p1 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --alignment ALIGNMENT --output_dir OUTPUT_DIR
# def processing_pipeline1(args, logger):
#     if args.transcripts != None and args.reference != None and args.annotation != None and args.alignment != None and args.output_dir != None and args.threads != None:
#         return args
#     else:
        #logger.error(message='Usage: python {} -p1 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --alignment ALIGNMENT --output_dir OUTPUT_DIR' \
        #      ' or other pipelines'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
        # logger.error(message='Usage: python {0} --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --alignment ALIGNMENT --output_dir OUTPUT_DIR' \
        #       ' or python {0} --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --output_dir OUTPUT_DIR'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
        # sys.exit(1)


#pipeline-2: python %(prog)s -p2 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --output_dir OUTPUT_DIR
# def processing_pipeline2(args, referenceFiles, logger):
#     if args.transcripts != None and args.reference != None and args.annotation != None and args.output_dir != None and args.threads != None:
#         args.alignment = align_fa_transcripts_to_psl_by_blat(args.transcripts, referenceFiles, args.output_dir, logger)
#         return args
#     else:
        #logger.error(message='Usage: python {} -p2 --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --output_dir OUTPUT_DIR' \
        #      ' or other pipelines'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
        # logger.error(message='Usage: python {0} --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --alignment ALIGNMENT --output_dir OUTPUT_DIR' \
        #       ' or python {0} --transcripts TRANSCRIPTS --reference REFERENCE --annotation ANNOTATION --output_dir OUTPUT_DIR'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
        # sys.exit(1)


#pipeline-3: python %(prog)s -p3 --reference REFERENCE --annotation ANNOTATION --assembler ASSEMBLER --reads READS --output_dir OUTPUT_DIR
# def processing_pipeline3(args, referenceFiles, logger):
#     if args.reference != None and args.annotation != None and args.assembler != None and \
#             ((args.left_reads != None and args.right_reads != None) or (args.paired_reads != None) or (args.single_reads != None)) \
#             and args.output_dir != None and args.threads != None:
#         args.transcripts = assemble_fq_reads_to_fa_transcripts(args, logger)
#         args.alignment = align_fa_transcripts_to_psl_by_blat(args.transcripts, referenceFiles, args.output_dir, logger)
#         return args
#     else:
#         logger.error(message='Usage: python {} -p3 --reference REFERENCE --annotation ANNOTATION --assembler ASSEMBLER --reads READS --output_dir OUTPUT_DIR' \
#               ' or other pipelines'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
#         sys.exit(1)


#pipeline-4: python %(prog)s -p4 --reference REFERENCE --annotation ANNOTATION --simulator SIMULATOR --filePAR FILEPAR --assembler ASSEMBLER
# def processing_pipeline4(args, referenceFiles, logger):
#     if args.reference != None and args.annotation != None and args.simulator != None and args.par != None and \
#                     args.assembler != None and args.output_dir != None and args.threads != None:
        # temporary solution (use single_reads or paired_reads, see par file for flux)
        # args.paired_reads = simulate_fq_reads_by_flux(args, logger)
        # args.transcripts = assemble_fq_reads_to_fa_transcripts(args, logger)
        # args.alignment = align_fa_transcripts_to_psl_by_blat(args.transcripts, referenceFiles, args.output_dir, logger)
        # return args
    # else:
    #     logger.error(message='Usage: python {} -p4 --reference REFERENCE --annotation ANNOTATION --simulator SIMULATOR --filePAR FILEPAR --assembler ASSEMBLER --output_dir OUTPUT_DIR' \
    #           ' or other pipelines'.format(sys.argv[0]), exit_with_code=1, to_stderr=True)
    #     sys.exit(1)


def get_default_folder_name_for_results(program_name):
    tmp = datetime.datetime.now()
    out_dir_name = os.path.join('{}_results'.format(program_name), 'results_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    return out_dir_name


def get_num_threads(threads, logger):
    if threads == None:
        try:
            threads = min(multiprocessing.cpu_count() / 2, 16)
        except:
            logger.warning('Failed to determine the number of CPUs')
            threads = rqconfig.DEFAULT_MAX_THREADS
        logger.info()
        logger.notice('Maximum number of threads is set to ' + str(threads) + ' (use --threads option to set it manually)')
    return threads


def process_labels(contigs_fpaths, labels, all_labels_from_dirs):
    # 1. labels if the provided by -l options
    if labels:
        # process duplicates, empties
        for i, label in enumerate(labels):
            if not label:
                labels[i] = quast.get_label_from_par_dir_and_fname(contigs_fpaths[i])

    # 2. labels from parent directories if -L flag was privided
    elif all_labels_from_dirs:
        labels = quast.get_labels_from_par_dirs(contigs_fpaths)

    # 3. otherwise, labels from fnames
    else:
        # labels from fname
        labels = [quast.qutils.rm_extentions_for_fasta_file(os.path.basename(fpath)) for fpath in contigs_fpaths]

        for duplicated_label in quast.get_duplicated(labels):
            for i, (label, fpath) in enumerate(zip(labels, contigs_fpaths)):
                if label == duplicated_label:
                    labels[i] = quast.get_label_from_par_dir_and_fname(contigs_fpaths[i])

    # fixing remaining duplicates by adding index
    for duplicated_label in quast.get_duplicated(labels):
        j = 0
        for i, (label, fpath) in enumerate(zip(labels, contigs_fpaths)):
            if label == duplicated_label:
                if j == 0:
                    labels[i] = label
                else:
                    labels[i] = label + '_' + str(j)
                j += 1
    return labels


def run_rnaQUAST_on_test_data(args, rquast_dirpath, program_name):
    transcripts0_path = os.path.join(rquast_dirpath, 'test_data', 'idba.fasta')
    transcripts1_path = os.path.join(rquast_dirpath, 'test_data', 'Trinity.fasta')
    transcripts2_path = os.path.join(rquast_dirpath, 'test_data', 'spades.311.fasta')

    args.transcripts = '{} {} {}'.format(transcripts0_path, transcripts1_path, transcripts2_path)

    args.reference = os.path.join(rquast_dirpath, 'test_data', 'Saccharomyces_cerevisiae.R64-1-1.75.dna.toplevel.fa')

    args.gene_database = os.path.join(rquast_dirpath, 'test_data', 'Saccharomyces_cerevisiae.R64-1-1.75.gtf')

    args.output_dir = '{}_test_output'.format(program_name)

    command = 'python {} --transcripts {} --reference {} --gene_database {} --output_dir {} --disable_infer_genes --disable_infer_transcripts'.\
        format(sys.argv[0], args.transcripts, args.reference, args.gene_database, args.output_dir)

    subprocess.call(command, shell=True)
    sys.exit(0)


def run_rnaQUAST_on_debug_data(args, rquast_dirpath, program_name):
    args.transcripts = os.path.join(rquast_dirpath, 'test_data', 'Trinity.fasta')

    args.reference = os.path.join(rquast_dirpath, 'test_data', 'Saccharomyces_cerevisiae.R64-1-1.75.dna.toplevel.fa')

    args.gene_database = os.path.join(rquast_dirpath, 'test_data', 'Saccharomyces_cerevisiae.R64-1-1.75.gtf')

    args.output_dir = '{}_debug_output'.format(program_name)

    command = 'python {} --transcripts {} --reference {} --gene_database {} --output_dir {} --debug --no_plots'.\
        format(sys.argv[0], args.transcripts, args.reference, args.gene_database, args.output_dir)

    subprocess.call(command, shell=True)
    sys.exit(0)


def create_output_folder(output_dir, program_name):
    # if --output_dir not use, create default folder for results:
    if output_dir == None:
        output_dir = get_default_folder_name_for_results(program_name)
        path_results = create_folder(os.path.split(output_dir)[0])
    # create output directory:
    output_dir = create_folder(output_dir)
    return output_dir


def create_separated_report_folders(args, transcripts_metrics, output_dir, label):
    # create output folder:
    current_out = create_empty_folder(os.path.join(output_dir, '{}_output'.format(label)))

    # create folders for metrics:
    basic_simple_dir, assembly_correctness_dir, assembly_completeness_dir = \
        create_metrics_folders(transcripts_metrics, current_out)

    # fusion_misassemble_dir = None
    # mapped_coverage_dir = None
    # if args.alignment != None and args.reference != None and args.transcripts != None:
        # create folder for fusions and misassemblies:
        # fusion_misassemble_dir = create_folder(os.path.join(current_out, 'fusions_misassemblies'))

    # if args.gene_database != None and args.alignment != None and args.reference != None and args.transcripts != None:
        # create folder for mapped coverages information:
        # mapped_coverage_dir = create_folder(os.path.join(current_out, 'mapped_coverages'))

    return current_out, basic_simple_dir, assembly_correctness_dir, assembly_completeness_dir
           # fusion_misassemble_dir, mapped_coverage_dir


def create_comparison_report_folders(transcripts_metrics, output_dir):
    #create output folder:
    current_out_dir = create_empty_folder(os.path.join(output_dir, 'comparison_output'))

    # create folders for metrics:
    basic_simple_dir, assembly_correctness_dir, assembly_completeness_dir = \
        create_metrics_folders(transcripts_metrics, current_out_dir)

    return current_out_dir, basic_simple_dir, assembly_correctness_dir, assembly_completeness_dir


def create_metrics_folders(transcripts_metrics, outdir):
    # BASIC AND SIMPLE:
    basic_simple_dir = None
    if transcripts_metrics.basic_metrics != None or transcripts_metrics.simple_metrics != None:
        basic_simple_dir = create_folder(os.path.join(outdir, 'basic'))

    assembly_correctness_dir = None
    assembly_completeness_dir = None
    if transcripts_metrics.assembly_correctness_metrics != None:
        # ASSEMBLY CORRECTNESS:
        assembly_correctness_dir = create_folder(os.path.join(outdir, 'specificity'))

    if transcripts_metrics.assembly_completeness_metrics != None or transcripts_metrics.cegma_metrics != None:
        # ASSEMBLY COMPLETENESS:
        assembly_completeness_dir = create_folder(os.path.join(outdir, 'sensitivity'))

    return basic_simple_dir, assembly_correctness_dir, assembly_completeness_dir


def create_folder(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def create_empty_folder(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)

    dir = create_folder(dir)

    return dir
